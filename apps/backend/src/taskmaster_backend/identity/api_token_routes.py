"""Organization-scoped API token management routes."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.identity.api_token_schemas import (
    ApiTokenCreateRequest,
    ApiTokenCreateResponse,
    ApiTokenListResponse,
    ApiTokenResponse,
)
from taskmaster_backend.identity.api_token_service import (
    create_organization_api_token,
    list_organization_api_tokens,
    revoke_organization_api_token,
)
from taskmaster_backend.identity.authorization import (
    authorize_principal,
    empty_permission_grants,
)
from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal, get_current_principal
from taskmaster_backend.identity.models import ApiToken
from taskmaster_backend.identity.permissions import api_token_management_requirement
from taskmaster_backend.identity.rbac import PermissionGrant
from taskmaster_backend.identity.schemas import ApiErrorResponse

router = APIRouter(
    prefix="/organizations/{organization_id}/api-tokens",
    tags=["api-tokens"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiTokenCreateResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ApiErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ApiErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ApiErrorResponse},
    },
    summary="Create organization API token",
)
def create_api_token(
    organization_id: str,
    request: ApiTokenCreateRequest,
    session: Session = Depends(get_db_session),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
    grants: Iterable[PermissionGrant] = Depends(empty_permission_grants),
) -> ApiTokenCreateResponse | JSONResponse:
    authorization_error = _authorize_api_token_management(organization_id, principal, grants)
    if authorization_error is not None:
        return authorization_error

    result = create_organization_api_token(
        session,
        organization_id=organization_id,
        request=request,
    )
    if result is None:
        return _not_found("organization_not_found", "Organization was not found.")

    return ApiTokenCreateResponse(
        api_token=ApiTokenResponse.model_validate(
            _api_token_response_dict(result.api_token)
        ),
        token=result.token,
    )


@router.get(
    "",
    response_model=ApiTokenListResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ApiErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ApiErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ApiErrorResponse},
    },
    summary="List organization API tokens",
)
def list_api_tokens(
    organization_id: str,
    session: Session = Depends(get_db_session),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
    grants: Iterable[PermissionGrant] = Depends(empty_permission_grants),
) -> ApiTokenListResponse | JSONResponse:
    authorization_error = _authorize_api_token_management(organization_id, principal, grants)
    if authorization_error is not None:
        return authorization_error

    api_tokens = list_organization_api_tokens(session, organization_id=organization_id)
    if api_tokens is None:
        return _not_found("organization_not_found", "Organization was not found.")

    return ApiTokenListResponse(
        items=[
            ApiTokenResponse.model_validate(_api_token_response_dict(api_token))
            for api_token in api_tokens
        ]
    )


@router.post(
    "/{api_token_id}/revoke",
    response_model=ApiTokenResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ApiErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ApiErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ApiErrorResponse},
    },
    summary="Revoke organization API token",
)
def revoke_api_token(
    organization_id: str,
    api_token_id: str,
    session: Session = Depends(get_db_session),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
    grants: Iterable[PermissionGrant] = Depends(empty_permission_grants),
) -> ApiTokenResponse | JSONResponse:
    authorization_error = _authorize_api_token_management(organization_id, principal, grants)
    if authorization_error is not None:
        return authorization_error

    api_token = revoke_organization_api_token(
        session,
        organization_id=organization_id,
        api_token_id=api_token_id,
    )
    if api_token is None:
        return _not_found("api_token_not_found", "API token was not found.")

    return ApiTokenResponse.model_validate(_api_token_response_dict(api_token))


def _authorize_api_token_management(
    organization_id: str,
    principal: AuthenticatedPrincipal,
    grants: Iterable[PermissionGrant],
) -> JSONResponse | None:
    try:
        requirement = api_token_management_requirement(organization_id)
    except ValueError:
        return _bad_request("invalid_organization_scope", "Organization scope is invalid.")

    authorize_principal(principal, requirement, grants)
    return None


def _api_token_response_dict(api_token: ApiToken) -> dict[str, object]:
    return {
        "id": api_token.id,
        "organization_id": api_token.organization_id,
        "name": api_token.name,
        "scopes": list(api_token.scopes),
        "expires_at": api_token.expires_at,
        "revoked_at": api_token.revoked_at,
        "last_used_at": api_token.last_used_at,
        "created_at": api_token.created_at,
        "updated_at": api_token.updated_at,
    }


def _bad_request(error_code: str, message: str) -> JSONResponse:
    return _error_response(status.HTTP_400_BAD_REQUEST, error_code, message)


def _not_found(error_code: str, message: str) -> JSONResponse:
    return _error_response(status.HTTP_404_NOT_FOUND, error_code, message)


def _error_response(http_status: int, error_code: str, message: str) -> JSONResponse:
    error = ApiErrorResponse(
        error_code=error_code,
        message=message,
        correlation_id=str(uuid4()),
    )
    return JSONResponse(status_code=http_status, content=error.model_dump())
