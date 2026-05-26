"""Tests for webhook delivery handler behavior."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.audit.models import EventOutbox
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization
from taskmaster_backend.integrations.delivery import (
    WebhookDeliveryError,
    WebhookDeliveryHandler,
    WebhookDeliveryRequest,
    WebhookDeliveryResult,
    build_webhook_delivery_request,
)
from taskmaster_backend.integrations.models import WebhookEndpoint


class StaticSecretProvider:
    def __init__(self) -> None:
        self.requested_references: list[str] = []

    def get_signing_secret(self, secret_reference: str) -> str:
        self.requested_references.append(secret_reference)
        return "whsec_signing_material"


class RecordingTransport:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code
        self.requests: list[WebhookDeliveryRequest] = []

    def deliver(self, request: WebhookDeliveryRequest) -> WebhookDeliveryResult:
        self.requests.append(request)
        return WebhookDeliveryResult(status_code=self.status_code)


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def _seed_scope(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        session.add(Organization(id="org-1", name="Acme"))
        session.commit()


def _add_event(session: Session) -> EventOutbox:
    event = EventOutbox(
        event_id="event-1",
        event_type="work_item.created",
        occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        actor_id=None,
        organization_id="org-1",
        workspace_id=None,
        project_id="project-1",
        entity_type="work_item",
        entity_id="work-item-1",
        correlation_id="correlation-1",
        payload={"work_item_id": "work-item-1"},
        payload_version="1.0",
    )
    session.add(event)
    return event


def _add_webhook(
    session: Session,
    *,
    webhook_id: str = "webhook-1",
    organization_id: str = "org-1",
    is_active: bool = True,
    event_types: list[str] | None = None,
    project_filters: list[str] | None = None,
) -> WebhookEndpoint:
    webhook = WebhookEndpoint(
        id=webhook_id,
        organization_id=organization_id,
        workspace_id=None,
        url=f"https://example.test/{webhook_id}",
        description=None,
        event_types=event_types or ["work_item.created"],
        project_filters=project_filters or [],
        is_active=is_active,
        secret_hash=f"sha256${webhook_id}",
        secret_reference=f"secret-ref-{webhook_id}",
    )
    session.add(webhook)
    return webhook


def test_build_webhook_delivery_request_contains_contract_fields_and_signature() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)
    secret_provider = StaticSecretProvider()

    with session_factory() as session:
        event = _add_event(session)
        webhook = _add_webhook(session)
        session.flush()
        request = build_webhook_delivery_request(
            event=event,
            webhook_endpoint=webhook,
            secret_provider=secret_provider,
        )

    body = json.loads(request.body.decode("utf-8"))
    assert request.url == "https://example.test/webhook-1"
    assert body["webhook_id"] == "webhook-1"
    assert body["event_id"] == "event-1"
    assert body["event_type"] == "work_item.created"
    assert body["payload_version"] == "1.0"
    assert body["payload"] == {"work_item_id": "work-item-1"}
    assert request.headers["x-taskmaster-delivery-id"] == body["delivery_id"]
    assert request.headers["x-taskmaster-signature"].startswith("sha256=")
    assert secret_provider.requested_references == ["secret-ref-webhook-1"]


def test_delivery_handler_sends_active_matching_organization_webhooks() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)
    secret_provider = StaticSecretProvider()
    transport = RecordingTransport()
    handler = WebhookDeliveryHandler(
        secret_provider=secret_provider,
        transport=transport,
    )

    with session_factory() as session:
        event = _add_event(session)
        _add_webhook(session)
        _add_webhook(session, webhook_id="webhook-inactive", is_active=False)
        session.commit()
        handler.handle(event, session)

    assert len(transport.requests) == 1
    assert transport.requests[0].url == "https://example.test/webhook-1"
    assert secret_provider.requested_references == ["secret-ref-webhook-1"]


def test_delivery_handler_ignores_other_organization_webhooks() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)
    transport = RecordingTransport()
    handler = WebhookDeliveryHandler(
        secret_provider=StaticSecretProvider(),
        transport=transport,
    )

    with session_factory() as session:
        event = _add_event(session)
        session.add(Organization(id="org-2", name="Globex"))
        _add_webhook(session, organization_id="org-2")
        session.commit()
        handler.handle(event, session)

    assert transport.requests == []


def test_delivery_handler_respects_event_type_and_project_filters() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)
    transport = RecordingTransport()
    handler = WebhookDeliveryHandler(
        secret_provider=StaticSecretProvider(),
        transport=transport,
    )

    with session_factory() as session:
        event = _add_event(session)
        _add_webhook(session, webhook_id="matching", project_filters=["project-1"])
        _add_webhook(session, webhook_id="wrong-event", event_types=["comment.created"])
        _add_webhook(session, webhook_id="wrong-project", project_filters=["project-2"])
        session.commit()
        handler.handle(event, session)

    assert [request.url for request in transport.requests] == [
        "https://example.test/matching",
    ]


def test_delivery_handler_raises_on_non_success_response() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)
    handler = WebhookDeliveryHandler(
        secret_provider=StaticSecretProvider(),
        transport=RecordingTransport(status_code=500),
    )

    with session_factory() as session:
        event = _add_event(session)
        _add_webhook(session)
        session.commit()
        try:
            handler.handle(event, session)
        except WebhookDeliveryError as exc:
            assert "webhook-1" in str(exc)
        else:
            raise AssertionError("expected WebhookDeliveryError")


def test_delivery_handler_does_not_mutate_outbox_status_directly() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)
    handler = WebhookDeliveryHandler(
        secret_provider=StaticSecretProvider(),
        transport=RecordingTransport(),
    )

    with session_factory() as session:
        event = _add_event(session)
        _add_webhook(session)
        session.commit()
        handler.handle(event, session)
        persisted_event = session.scalars(select(EventOutbox)).one()

    assert persisted_event.status == "pending"
    assert persisted_event.dispatched_at is None
