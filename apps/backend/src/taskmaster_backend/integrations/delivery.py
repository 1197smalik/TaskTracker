"""Webhook delivery handler for outbox-dispatched domain events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskmaster_backend.audit.models import EventOutbox
from taskmaster_backend.integrations.models import WebhookEndpoint
from taskmaster_backend.integrations.signing import sign_webhook_payload
from taskmaster_backend.integrations.webhook_secrets import WebhookSecretProvider


@dataclass(frozen=True, slots=True)
class WebhookDeliveryRequest:
    url: str
    body: bytes
    headers: dict[str, str]


@dataclass(frozen=True, slots=True)
class WebhookDeliveryResult:
    status_code: int


class WebhookTransport(Protocol):
    """Network adapter for webhook delivery attempts."""

    def deliver(self, request: WebhookDeliveryRequest) -> WebhookDeliveryResult:
        """Deliver one signed webhook request."""


class WebhookDeliveryError(RuntimeError):
    """Raised when one or more webhook deliveries fail."""


class WebhookDeliveryHandler:
    """Outbox handler that sends signed webhook deliveries."""

    def __init__(
        self,
        *,
        secret_provider: WebhookSecretProvider,
        transport: WebhookTransport,
    ) -> None:
        self._secret_provider = secret_provider
        self._transport = transport

    def handle(self, event: EventOutbox, session: Session) -> None:
        failed_webhook_ids: list[str] = []
        for webhook_endpoint in _matching_webhook_endpoints(session, event):
            request = build_webhook_delivery_request(
                event=event,
                webhook_endpoint=webhook_endpoint,
                secret_provider=self._secret_provider,
            )
            result = self._transport.deliver(request)
            if result.status_code < 200 or result.status_code >= 300:
                failed_webhook_ids.append(webhook_endpoint.id)

        if failed_webhook_ids:
            raise WebhookDeliveryError(
                "webhook delivery failed for webhook_ids="
                + ",".join(failed_webhook_ids)
            )


def build_webhook_delivery_request(
    *,
    event: EventOutbox,
    webhook_endpoint: WebhookEndpoint,
    secret_provider: WebhookSecretProvider,
) -> WebhookDeliveryRequest:
    """Build one signed webhook delivery request without performing I/O."""
    delivery_id = str(uuid4())
    body = _serialize_delivery_body(
        {
            "webhook_id": webhook_endpoint.id,
            "delivery_id": delivery_id,
            "event_id": event.event_id,
            "event_type": event.event_type,
            "occurred_at": _datetime_to_iso(event.occurred_at),
            "payload_version": event.payload_version,
            "payload": event.payload,
        }
    )
    signature = sign_webhook_payload(
        secret_provider=secret_provider,
        secret_reference=webhook_endpoint.secret_reference,
        payload=body,
    )
    return WebhookDeliveryRequest(
        url=webhook_endpoint.url,
        body=body,
        headers={
            "content-type": "application/json",
            "x-taskmaster-delivery-id": delivery_id,
            "x-taskmaster-event-id": event.event_id,
            "x-taskmaster-event-type": event.event_type,
            "x-taskmaster-signature": signature.header_value,
        },
    )


def _matching_webhook_endpoints(
    session: Session,
    event: EventOutbox,
) -> list[WebhookEndpoint]:
    candidates = list(
        session.scalars(
            select(WebhookEndpoint)
            .where(WebhookEndpoint.organization_id == event.organization_id)
            .where(WebhookEndpoint.is_active.is_(True))
            .order_by(WebhookEndpoint.created_at.asc(), WebhookEndpoint.id.asc())
        )
    )
    return [
        webhook_endpoint
        for webhook_endpoint in candidates
        if _subscribes_to_event(webhook_endpoint, event)
    ]


def _subscribes_to_event(
    webhook_endpoint: WebhookEndpoint,
    event: EventOutbox,
) -> bool:
    if event.event_type not in webhook_endpoint.event_types:
        return False
    if (
        webhook_endpoint.workspace_id is not None
        and webhook_endpoint.workspace_id != event.workspace_id
    ):
        return False
    if (
        webhook_endpoint.project_filters
        and event.project_id not in webhook_endpoint.project_filters
    ):
        return False
    return True


def _serialize_delivery_body(body: dict[str, object]) -> bytes:
    return json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _datetime_to_iso(value: datetime) -> str:
    return value.isoformat()
