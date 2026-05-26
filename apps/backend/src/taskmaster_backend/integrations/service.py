"""Application service for webhook endpoint management."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from taskmaster_backend.integrations.models import WebhookEndpoint
from taskmaster_backend.integrations.repository import (
    create_webhook_endpoint_record,
    get_webhook_endpoint_for_organization,
    list_webhook_endpoints_for_organization,
    organization_exists,
    workspace_belongs_to_organization,
)
from taskmaster_backend.integrations.schemas import WebhookEndpointCreateRequest
from taskmaster_backend.integrations.webhook_secrets import WebhookSecretIssuer

WEBHOOK_ERROR_ORGANIZATION_NOT_FOUND = "organization_not_found"
WEBHOOK_ERROR_INVALID_WORKSPACE_SCOPE = "invalid_workspace_scope"
WEBHOOK_ERROR_WEBHOOK_NOT_FOUND = "webhook_not_found"


@dataclass(frozen=True, slots=True)
class WebhookEndpointCreateResult:
    webhook_endpoint: WebhookEndpoint
    secret: str


@dataclass(frozen=True, slots=True)
class WebhookEndpointServiceError:
    error_code: str
    message: str


def create_organization_webhook_endpoint(
    session: Session,
    *,
    webhook_id: str,
    organization_id: str,
    request: WebhookEndpointCreateRequest,
    secret_issuer: WebhookSecretIssuer,
) -> WebhookEndpointCreateResult | WebhookEndpointServiceError:
    if not organization_exists(session, organization_id):
        return WebhookEndpointServiceError(
            error_code=WEBHOOK_ERROR_ORGANIZATION_NOT_FOUND,
            message="Organization was not found.",
        )
    if request.workspace_id is not None and not workspace_belongs_to_organization(
        session,
        organization_id=organization_id,
        workspace_id=request.workspace_id,
    ):
        return WebhookEndpointServiceError(
            error_code=WEBHOOK_ERROR_INVALID_WORKSPACE_SCOPE,
            message="Workspace scope is invalid.",
        )

    secret_result = secret_issuer.create_webhook_secret(webhook_id)
    webhook_endpoint = create_webhook_endpoint_record(
        session,
        webhook_id=webhook_id,
        organization_id=organization_id,
        workspace_id=request.workspace_id,
        url=request.url,
        description=request.description,
        event_types=request.event_types,
        project_filters=request.project_filters,
        secret_hash=secret_result.secret_hash,
        secret_reference=secret_result.secret_reference,
    )
    return WebhookEndpointCreateResult(
        webhook_endpoint=webhook_endpoint,
        secret=secret_result.raw_secret,
    )


def list_organization_webhook_endpoints(
    session: Session,
    *,
    organization_id: str,
) -> list[WebhookEndpoint] | WebhookEndpointServiceError:
    if not organization_exists(session, organization_id):
        return WebhookEndpointServiceError(
            error_code=WEBHOOK_ERROR_ORGANIZATION_NOT_FOUND,
            message="Organization was not found.",
        )
    return list_webhook_endpoints_for_organization(
        session,
        organization_id=organization_id,
    )


def revoke_organization_webhook_endpoint(
    session: Session,
    *,
    organization_id: str,
    webhook_endpoint_id: str,
) -> WebhookEndpoint | WebhookEndpointServiceError:
    if not organization_exists(session, organization_id):
        return WebhookEndpointServiceError(
            error_code=WEBHOOK_ERROR_ORGANIZATION_NOT_FOUND,
            message="Organization was not found.",
        )

    webhook_endpoint = get_webhook_endpoint_for_organization(
        session,
        organization_id=organization_id,
        webhook_endpoint_id=webhook_endpoint_id,
    )
    if webhook_endpoint is None:
        return WebhookEndpointServiceError(
            error_code=WEBHOOK_ERROR_WEBHOOK_NOT_FOUND,
            message="Webhook endpoint was not found.",
        )
    if webhook_endpoint.is_active:
        webhook_endpoint.is_active = False
        session.commit()
        session.refresh(webhook_endpoint)
    return webhook_endpoint
