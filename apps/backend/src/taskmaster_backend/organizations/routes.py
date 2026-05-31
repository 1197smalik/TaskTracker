"""Organization creation routes."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal, get_current_principal
from taskmaster_backend.identity.models import Organization, User
from taskmaster_backend.identity.schemas import ApiErrorResponse
from taskmaster_backend.organizations.schemas import (
    OrganizationCreateRequest,
    OrganizationCreateResponse,
    OrganizationResponse,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=OrganizationCreateResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ApiErrorResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": ApiErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ApiErrorResponse},
    },
    summary="Create organization",
    description=(
        "Create a Phase 1 organization for the authenticated principal. Workspace "
        "creation and advanced membership management are handled by later stories."
    ),
)
def create_organization(
    request: OrganizationCreateRequest,
    session: Session = Depends(get_db_session),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> OrganizationCreateResponse | JSONResponse:
    actor = session.get(User, principal.subject)
    if actor is None:
        return _error_response(
            status.HTTP_401_UNAUTHORIZED,
            error_code="invalid_session",
            message="Session is invalid. Sign in again.",
        )

    validation_error = _validate_name(request.name)
    if validation_error is not None:
        return validation_error

    assert request.name is not None
    normalized_name = request.name.strip()

    existing_organization = session.scalar(
        select(Organization).where(
            func.lower(func.trim(Organization.name)) == normalized_name.lower()
        )
    )
    if existing_organization is not None:
        return _error_response(
            status.HTTP_409_CONFLICT,
            error_code="duplicate_organization_name",
            message="Organization name is already in use.",
            field_errors={"name": ["Choose a different organization name."]},
        )

    organization = Organization(name=normalized_name, owner_user_id=actor.id)
    session.add(organization)
    session.commit()
    session.refresh(organization)

    return OrganizationCreateResponse(
        organization=OrganizationResponse(
            id=organization.id,
            name=organization.name,
            created_at=organization.created_at,
            updated_at=organization.updated_at,
        )
    )


def _validate_name(name: str | None) -> JSONResponse | None:
    if name is None or name.strip() == "":
        return _error_response(
            status.HTTP_400_BAD_REQUEST,
            error_code="invalid_organization_name",
            message="Organization name is required.",
            field_errors={"name": ["Enter an organization name."]},
        )

    normalized_name = name.strip()
    if len(normalized_name) < 3:
        return _error_response(
            status.HTTP_400_BAD_REQUEST,
            error_code="invalid_organization_name",
            message="Organization name must be at least 3 characters.",
            field_errors={"name": ["Use at least 3 characters."]},
        )

    if len(normalized_name) > 255:
        return _error_response(
            status.HTTP_400_BAD_REQUEST,
            error_code="invalid_organization_name",
            message="Organization name must be 255 characters or fewer.",
            field_errors={"name": ["Use 255 characters or fewer."]},
        )

    return None


def _error_response(
    http_status: int,
    *,
    error_code: str,
    message: str,
    field_errors: dict[str, list[str]] | None = None,
) -> JSONResponse:
    error = ApiErrorResponse(
        error_code=error_code,
        message=message,
        correlation_id=str(uuid4()),
        field_errors=field_errors or {},
    )
    return JSONResponse(status_code=http_status, content=error.model_dump())
