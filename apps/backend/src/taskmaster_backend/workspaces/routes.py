"""Workspace creation routes."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal, get_current_principal
from taskmaster_backend.identity.models import Organization, Workspace
from taskmaster_backend.identity.schemas import ApiErrorResponse
from taskmaster_backend.workspaces.schemas import (
    WorkspaceCreateRequest,
    WorkspaceCreateResponse,
    WorkspaceResponse,
)

router = APIRouter(
    prefix="/organizations/{organization_id}/workspaces",
    tags=["workspaces"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=WorkspaceCreateResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ApiErrorResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": ApiErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ApiErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ApiErrorResponse},
    },
    summary="Create workspace",
    description=(
        "Create a Phase 1 workspace within an authorized organization context. "
        "Project creation and advanced workspace settings are handled by later stories."
    ),
)
def create_workspace(
    organization_id: str,
    request: WorkspaceCreateRequest,
    session: Session = Depends(get_db_session),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> WorkspaceCreateResponse | JSONResponse:
    validation_error = _validate_name(request.name)
    if validation_error is not None:
        return validation_error

    organization = session.get(Organization, organization_id)
    if organization is None:
        return _error_response(
            status.HTTP_404_NOT_FOUND,
            error_code="organization_not_found",
            message="Organization was not found.",
        )
    if organization.owner_user_id != principal.subject:
        return _error_response(
            status.HTTP_403_FORBIDDEN,
            error_code="organization_access_denied",
            message="You are not authorized to create workspaces in this organization.",
        )

    assert request.name is not None
    workspace = Workspace(
        organization_id=organization.id,
        name=request.name.strip(),
    )
    session.add(workspace)
    session.commit()
    session.refresh(workspace)

    return WorkspaceCreateResponse(
        workspace=WorkspaceResponse(
            id=workspace.id,
            organization_id=workspace.organization_id,
            name=workspace.name,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )
    )


def _validate_name(name: str | None) -> JSONResponse | None:
    if name is None or name.strip() == "":
        return _error_response(
            status.HTTP_400_BAD_REQUEST,
            error_code="invalid_workspace_name",
            message="Workspace name is required.",
            field_errors={"name": ["Enter a workspace name."]},
        )

    normalized_name = name.strip()
    if len(normalized_name) < 3:
        return _error_response(
            status.HTTP_400_BAD_REQUEST,
            error_code="invalid_workspace_name",
            message="Workspace name must be at least 3 characters.",
            field_errors={"name": ["Use at least 3 characters."]},
        )

    if len(normalized_name) > 255:
        return _error_response(
            status.HTTP_400_BAD_REQUEST,
            error_code="invalid_workspace_name",
            message="Workspace name must be 255 characters or fewer.",
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
