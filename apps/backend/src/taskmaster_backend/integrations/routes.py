"""Organization-scoped webhook management routes."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.identity.authorization import (
    authorize_principal,
    empty_permission_grants,
)
from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal, get_current_principal
from taskmaster_backend.identity.rbac import PermissionGrant
from taskmaster_backend.identity.schemas import ApiErrorResponse
from taskmaster_backend.integrations.models import WebhookEndpoint
from taskmaster_backend.integrations.permissions import webhook_management_requirement
from taskmaster_backend.integrations.schemas import (
    WebhookEndpointCreateRequest,
    WebhookEndpointCreateResponse,
    WebhookEndpointListResponse,
    WebhookEndpointResponse,
)
from taskmaster_backend.integrations.service import (
    WEBHOOK_ERROR_INVALID_WORKSPACE_SCOPE,
    WEBHOOK_ERROR_ORGANIZATION_NOT_FOUND,
    WEBHOOK_ERROR_WEBHOOK_NOT_FOUND,
    WebhookEndpointServiceError,
    create_organization_webhook_endpoint,
    list_organization_webhook_endpoints,
    revoke_organization_webhook_endpoint,
)
from taskmaster_backend.integrations.webhook_secrets import (
    WebhookSecretCreateResult,
    WebhookSecretIssuer,
)

router = APIRouter(
    prefix="/organizations/{organization_id}/webhooks",
    tags=["webhooks"],
)


class WebhookSecretIssuerNotConfigured(RuntimeError):
    """Raised when webhook management is used without secret storage configured."""


class _UnconfiguredWebhookSecretIssuer:
    def create_webhook_secret(self, webhook_id: str) -> WebhookSecretCreateResult:
        raise WebhookSecretIssuerNotConfigured("webhook secret issuer is not configured")


def get_webhook_secret_issuer() -> WebhookSecretIssuer:
    """Default dependency fails closed until a real secret issuer is configured."""
    return _UnconfiguredWebhookSecretIssuer()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=WebhookEndpointCreateResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ApiErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ApiErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ApiErrorResponse},
        status.HTTP_501_NOT_IMPLEMENTED: {"model": ApiErrorResponse},
    },
    summary="Create organization webhook endpoint",
)
def create_webhook_endpoint(
    organization_id: str,
    request: WebhookEndpointCreateRequest,
    session: Session = Depends(get_db_session),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
    grants: Iterable[PermissionGrant] = Depends(empty_permission_grants),
    secret_issuer: WebhookSecretIssuer = Depends(get_webhook_secret_issuer),
) -> WebhookEndpointCreateResponse | JSONResponse:
    authorization_error = _authorize_webhook_management(organization_id, principal, grants)
    if authorization_error is not None:
        return authorization_error

    try:
        result = create_organization_webhook_endpoint(
            session,
            webhook_id=str(uuid4()),
            organization_id=organization_id,
            request=request,
            secret_issuer=secret_issuer,
        )
    except WebhookSecretIssuerNotConfigured:
        return _error_response(
            status.HTTP_501_NOT_IMPLEMENTED,
            "webhook_secret_issuer_not_configured",
            "Webhook secret issuer is not configured.",
        )
    if isinstance(result, WebhookEndpointServiceError):
        return _service_error_response(result)

    return WebhookEndpointCreateResponse(
        webhook_endpoint=WebhookEndpointResponse.model_validate(
            _webhook_endpoint_response_dict(result.webhook_endpoint)
        ),
        secret=result.secret,
    )


@router.get(
    "",
    response_model=WebhookEndpointListResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ApiErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ApiErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ApiErrorResponse},
    },
    summary="List organization webhook endpoints",
)
def list_webhook_endpoints(
    organization_id: str,
    session: Session = Depends(get_db_session),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
    grants: Iterable[PermissionGrant] = Depends(empty_permission_grants),
) -> WebhookEndpointListResponse | JSONResponse:
    authorization_error = _authorize_webhook_management(organization_id, principal, grants)
    if authorization_error is not None:
        return authorization_error

    result = list_organization_webhook_endpoints(session, organization_id=organization_id)
    if isinstance(result, WebhookEndpointServiceError):
        return _service_error_response(result)

    return WebhookEndpointListResponse(
        items=[
            WebhookEndpointResponse.model_validate(
                _webhook_endpoint_response_dict(webhook_endpoint)
            )
            for webhook_endpoint in result
        ]
    )


@router.post(
    "/{webhook_endpoint_id}/revoke",
    response_model=WebhookEndpointResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ApiErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ApiErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ApiErrorResponse},
    },
    summary="Revoke organization webhook endpoint",
)
def revoke_webhook_endpoint(
    organization_id: str,
    webhook_endpoint_id: str,
    session: Session = Depends(get_db_session),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
    grants: Iterable[PermissionGrant] = Depends(empty_permission_grants),
) -> WebhookEndpointResponse | JSONResponse:
    authorization_error = _authorize_webhook_management(organization_id, principal, grants)
    if authorization_error is not None:
        return authorization_error

    result = revoke_organization_webhook_endpoint(
        session,
        organization_id=organization_id,
        webhook_endpoint_id=webhook_endpoint_id,
    )
    if isinstance(result, WebhookEndpointServiceError):
        return _service_error_response(result)

    return WebhookEndpointResponse.model_validate(_webhook_endpoint_response_dict(result))


def _authorize_webhook_management(
    organization_id: str,
    principal: AuthenticatedPrincipal,
    grants: Iterable[PermissionGrant],
) -> JSONResponse | None:
    try:
        requirement = webhook_management_requirement(organization_id)
    except ValueError:
        return _error_response(
            status.HTTP_400_BAD_REQUEST,
            "invalid_organization_scope",
            "Organization scope is invalid.",
        )

    authorize_principal(principal, requirement, grants)
    return None


def _webhook_endpoint_response_dict(
    webhook_endpoint: WebhookEndpoint,
) -> dict[str, object]:
    return {
        "id": webhook_endpoint.id,
        "organization_id": webhook_endpoint.organization_id,
        "workspace_id": webhook_endpoint.workspace_id,
        "url": webhook_endpoint.url,
        "description": webhook_endpoint.description,
        "event_types": list(webhook_endpoint.event_types),
        "project_filters": list(webhook_endpoint.project_filters),
        "is_active": webhook_endpoint.is_active,
        "created_at": webhook_endpoint.created_at,
        "updated_at": webhook_endpoint.updated_at,
    }


def _service_error_response(error: WebhookEndpointServiceError) -> JSONResponse:
    if error.error_code == WEBHOOK_ERROR_INVALID_WORKSPACE_SCOPE:
        return _error_response(status.HTTP_400_BAD_REQUEST, error.error_code, error.message)
    if error.error_code in {
        WEBHOOK_ERROR_ORGANIZATION_NOT_FOUND,
        WEBHOOK_ERROR_WEBHOOK_NOT_FOUND,
    }:
        return _error_response(status.HTTP_404_NOT_FOUND, error.error_code, error.message)
    return _error_response(status.HTTP_400_BAD_REQUEST, error.error_code, error.message)


def _error_response(http_status: int, error_code: str, message: str) -> JSONResponse:
    error = ApiErrorResponse(
        error_code=error_code,
        message=message,
        correlation_id=str(uuid4()),
    )
    return JSONResponse(status_code=http_status, content=error.model_dump())
