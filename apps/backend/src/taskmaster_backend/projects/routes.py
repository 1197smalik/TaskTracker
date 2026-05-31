"""Project-domain API routes."""

from __future__ import annotations

import re
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal, get_current_principal
from taskmaster_backend.identity.models import Organization, Workspace
from taskmaster_backend.projects.models import Project
from taskmaster_backend.projects.schemas import (
    ProjectApiErrorResponse,
    ProjectComponentCreateRequest,
    ProjectComponentListResponse,
    ProjectComponentResponse,
    ProjectCreateRequest,
    ProjectCreateResponse,
    ProjectLabelCreateRequest,
    ProjectLabelListResponse,
    ProjectLabelResponse,
    ProjectNavigationListResponse,
    ProjectNavigationResponse,
    ProjectResponse,
    ProjectVersionCreateRequest,
    ProjectVersionListResponse,
    ProjectVersionResponse,
    ProjectWorkflowStateCatalogResponse,
    ProjectWorkflowStateResponse,
    WorkspaceNavigationListResponse,
    WorkspaceNavigationResponse,
)
from taskmaster_backend.workflows.repository import (
    PROJECT_NOT_FOUND,
    WORKFLOW_ASSIGNMENT_NOT_FOUND,
    WORKFLOW_DEFINITION_NOT_FOUND,
    list_project_workflow_state_catalog,
)

router = APIRouter(prefix="/projects", tags=["projects"])
PROJECT_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*$")


@router.get(
    "/workspaces",
    response_model=WorkspaceNavigationListResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ProjectApiErrorResponse},
    },
    summary="List workspaces for local navigation",
    description=(
        "List minimal workspace navigation records filtered by the backend-owned "
        "Phase 1 organization visibility rules for the authenticated principal."
    ),
)
def list_workspaces_route(
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
    session: Session = Depends(get_db_session),
) -> WorkspaceNavigationListResponse:
    workspaces = (
        session.query(Workspace)
        .join(Organization, Organization.id == Workspace.organization_id)
        .filter(Organization.owner_user_id == principal.subject)
        .order_by(Workspace.name.asc(), Workspace.id.asc())
        .all()
    )
    return WorkspaceNavigationListResponse(
        items=[
            WorkspaceNavigationResponse(
                id=workspace.id,
                organization_id=workspace.organization_id,
                name=workspace.name,
            )
            for workspace in workspaces
        ]
    )


@router.get(
    "/workspaces/{workspace_id}/projects",
    response_model=ProjectNavigationListResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ProjectApiErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ProjectApiErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ProjectApiErrorResponse},
    },
    summary="List projects for a workspace for local navigation",
    description=(
        "List minimal project navigation records for a selected workspace that is "
        "visible to the authenticated principal under the backend-owned Phase 1 "
        "organization visibility rules."
    ),
)
def list_workspace_projects_route(
    workspace_id: str,
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
    session: Session = Depends(get_db_session),
) -> ProjectNavigationListResponse | JSONResponse:
    workspace, organization, error_response = _resolve_owned_workspace(
        session,
        workspace_id,
        principal.subject,
    )
    if error_response is not None:
        return error_response

    assert workspace is not None
    assert organization is not None

    projects = (
        session.query(Project)
        .filter(Project.workspace_id == workspace.id)
        .order_by(Project.key.asc(), Project.id.asc())
        .all()
    )
    return ProjectNavigationListResponse(
        items=[
            ProjectNavigationResponse(
                id=project.id,
                workspace_id=project.workspace_id,
                key=project.key,
                name=project.name,
            )
            for project in projects
        ]
    )


@router.post(
    "/workspaces/{workspace_id}/projects",
    status_code=status.HTTP_201_CREATED,
    response_model=ProjectCreateResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ProjectApiErrorResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": ProjectApiErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ProjectApiErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ProjectApiErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ProjectApiErrorResponse},
    },
    summary="Create project",
    description=(
        "Create a Phase 1 project within an authorized workspace context. "
        "Project administration, boards, and work item wiring are handled by later stories."
    ),
)
def create_project_route(
    workspace_id: str,
    request: ProjectCreateRequest,
    session: Session = Depends(get_db_session),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> ProjectCreateResponse | JSONResponse:
    normalized_key, normalized_name, validation_error = _validate_project_request(
        request.key,
        request.name,
    )
    if validation_error is not None:
        return validation_error

    workspace, organization, error_response = _resolve_owned_workspace(
        session,
        workspace_id,
        principal.subject,
    )
    if error_response is not None:
        return error_response

    assert normalized_key is not None
    assert normalized_name is not None
    assert workspace is not None
    assert organization is not None

    duplicate_project_key = (
        session.query(Project.id)
        .filter(Project.workspace_id == workspace.id)
        .filter(func.lower(Project.key) == normalized_key.lower())
        .first()
    )
    if duplicate_project_key is not None:
        return _project_error_response(
            status.HTTP_409_CONFLICT,
            error_code="duplicate_project_key",
            message="Project key already exists in this workspace.",
            field_errors={"key": ["Use a unique project key."]},
        )

    duplicate_project_name = (
        session.query(Project.id)
        .filter(Project.workspace_id == workspace.id)
        .filter(func.lower(Project.name) == normalized_name.lower())
        .first()
    )
    if duplicate_project_name is not None:
        return _project_error_response(
            status.HTTP_409_CONFLICT,
            error_code="duplicate_project_name",
            message="Project name already exists in this workspace.",
            field_errors={"name": ["Use a unique project name."]},
        )

    project = Project(
        workspace_id=workspace.id,
        key=normalized_key,
        name=normalized_name,
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    return ProjectCreateResponse(
        project=ProjectResponse(
            id=project.id,
            workspace_id=project.workspace_id,
            key=project.key,
            name=project.name,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
    )


def _labels_not_implemented_error() -> ProjectApiErrorResponse:
    return ProjectApiErrorResponse(
        error_code="project_labels_not_implemented",
        message="Project label persistence is not available yet.",
        details={
            "reason": (
                "Label storage and persistence wiring are intentionally "
                "deferred to later stories."
            ),
        },
        correlation_id=str(uuid4()),
    )


def _components_not_implemented_error() -> ProjectApiErrorResponse:
    return ProjectApiErrorResponse(
        error_code="project_components_not_implemented",
        message="Project component persistence is not available yet.",
        details={
            "reason": (
                "Component storage and persistence wiring are intentionally "
                "deferred to later stories."
            ),
        },
        correlation_id=str(uuid4()),
    )


def _versions_not_implemented_error() -> ProjectApiErrorResponse:
    return ProjectApiErrorResponse(
        error_code="project_versions_not_implemented",
        message="Project version persistence is not available yet.",
        details={
            "reason": (
                "Version storage and persistence wiring are intentionally "
                "deferred until the backing schema story is implemented."
            ),
        },
        correlation_id=str(uuid4()),
    )


def _project_not_found_error() -> ProjectApiErrorResponse:
    return ProjectApiErrorResponse(
        error_code="project_not_found",
        message="Project was not found or is inaccessible.",
        correlation_id=str(uuid4()),
    )


def _workflow_assignment_not_found_error() -> ProjectApiErrorResponse:
    return ProjectApiErrorResponse(
        error_code="workflow_assignment_not_found",
        message="Project does not have an assigned workflow.",
        correlation_id=str(uuid4()),
    )


def _workflow_definition_not_found_error() -> ProjectApiErrorResponse:
    return ProjectApiErrorResponse(
        error_code="workflow_definition_not_found",
        message="Assigned workflow definition was not found or is inaccessible.",
        correlation_id=str(uuid4()),
    )


def _resolve_owned_workspace(
    session: Session,
    workspace_id: str,
    principal_subject: str,
) -> tuple[Workspace | None, Organization | None, JSONResponse | None]:
    workspace = session.get(Workspace, workspace_id)
    if workspace is None:
        return (
            None,
            None,
            _project_error_response(
                status.HTTP_404_NOT_FOUND,
                error_code="workspace_not_found",
                message="Workspace was not found.",
            ),
        )

    organization = session.get(Organization, workspace.organization_id)
    if organization is None:
        return (
            None,
            None,
            _project_error_response(
                status.HTTP_404_NOT_FOUND,
                error_code="workspace_not_found",
                message="Workspace was not found.",
            ),
        )
    if organization.owner_user_id != principal_subject:
        return (
            None,
            None,
            _project_error_response(
                status.HTTP_403_FORBIDDEN,
                error_code="workspace_access_denied",
                message="You are not authorized to access this workspace.",
            ),
        )

    return workspace, organization, None


def _validate_project_request(
    key: str | None,
    name: str | None,
) -> tuple[str | None, str | None, JSONResponse | None]:
    if key is None or key.strip() == "":
        return (
            None,
            None,
            _project_error_response(
                status.HTTP_400_BAD_REQUEST,
                error_code="invalid_project_key",
                message="Project key is required.",
                field_errors={"key": ["Enter a project key."]},
            ),
        )

    normalized_key = key.strip().upper()
    if len(normalized_key) < 2:
        return (
            None,
            None,
            _project_error_response(
                status.HTTP_400_BAD_REQUEST,
                error_code="invalid_project_key",
                message="Project key must be at least 2 characters.",
                field_errors={"key": ["Use at least 2 characters."]},
            ),
        )
    if len(normalized_key) > 32:
        return (
            None,
            None,
            _project_error_response(
                status.HTTP_400_BAD_REQUEST,
                error_code="invalid_project_key",
                message="Project key must be 32 characters or fewer.",
                field_errors={"key": ["Use 32 characters or fewer."]},
            ),
        )
    if PROJECT_KEY_PATTERN.fullmatch(normalized_key) is None:
        return (
            None,
            None,
            _project_error_response(
                status.HTTP_400_BAD_REQUEST,
                error_code="invalid_project_key",
                message="Project key must use letters, numbers, or hyphens.",
                field_errors={"key": ["Use letters, numbers, or hyphens only."]},
            ),
        )

    if name is None or name.strip() == "":
        return (
            None,
            None,
            _project_error_response(
                status.HTTP_400_BAD_REQUEST,
                error_code="invalid_project_name",
                message="Project name is required.",
                field_errors={"name": ["Enter a project name."]},
            ),
        )

    normalized_name = name.strip()
    if len(normalized_name) < 3:
        return (
            None,
            None,
            _project_error_response(
                status.HTTP_400_BAD_REQUEST,
                error_code="invalid_project_name",
                message="Project name must be at least 3 characters.",
                field_errors={"name": ["Use at least 3 characters."]},
            ),
        )
    if len(normalized_name) > 255:
        return (
            None,
            None,
            _project_error_response(
                status.HTTP_400_BAD_REQUEST,
                error_code="invalid_project_name",
                message="Project name must be 255 characters or fewer.",
                field_errors={"name": ["Use 255 characters or fewer."]},
            ),
        )

    return normalized_key, normalized_name, None


def _project_error_response(
    http_status: int,
    *,
    error_code: str,
    message: str,
    field_errors: dict[str, list[str]] | None = None,
) -> JSONResponse:
    error = ProjectApiErrorResponse(
        error_code=error_code,
        message=message,
        correlation_id=str(uuid4()),
        field_errors=field_errors or {},
    )
    return JSONResponse(status_code=http_status, content=error.model_dump())


@router.get(
    "/{project_id}/workflow-states",
    response_model=ProjectWorkflowStateCatalogResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ProjectApiErrorResponse,
            "description": "Project workflow state catalog was not found.",
        },
    },
    summary="List project workflow states",
    description=(
        "List the backend-owned ordered workflow states for a project's assigned "
        "workflow. This exposes board column mapping inputs only; transition "
        "legality, permissions, board preferences, and workflow editing are handled "
        "by separate contracts."
    ),
)
def list_project_workflow_states_route(
    project_id: str,
    session: Session = Depends(get_db_session),
) -> ProjectWorkflowStateCatalogResponse | JSONResponse:
    workflow_definition, workflow_states, error = list_project_workflow_state_catalog(
        session,
        project_id,
    )

    if error == PROJECT_NOT_FOUND:
        response_error = _project_not_found_error()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=response_error.model_dump(),
        )
    if error == WORKFLOW_ASSIGNMENT_NOT_FOUND:
        response_error = _workflow_assignment_not_found_error()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=response_error.model_dump(),
        )
    if error == WORKFLOW_DEFINITION_NOT_FOUND:
        response_error = _workflow_definition_not_found_error()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=response_error.model_dump(),
        )

    assert workflow_definition is not None
    return ProjectWorkflowStateCatalogResponse(
        workflow_definition_id=workflow_definition.id,
        states=[
            ProjectWorkflowStateResponse.from_model(workflow_state)
            for workflow_state in workflow_states
        ],
    )


@router.get(
    "/{project_id}/labels",
    response_model=ProjectLabelListResponse,
    responses={
        status.HTTP_501_NOT_IMPLEMENTED: {
            "model": ProjectApiErrorResponse,
            "description": "Project label listing is defined but not implemented yet.",
        },
    },
    summary="List project labels",
    description=(
        "Versioned project label listing contract. Label persistence and retrieval are "
        "intentionally deferred until the backing schema and data access stories."
    ),
)
def list_project_labels(project_id: str) -> JSONResponse:
    _ = project_id
    error = _labels_not_implemented_error()
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content=error.model_dump(),
    )


@router.post(
    "/{project_id}/labels",
    response_model=ProjectLabelResponse,
    responses={
        status.HTTP_501_NOT_IMPLEMENTED: {
            "model": ProjectApiErrorResponse,
            "description": "Project label creation is defined but not implemented yet.",
        },
    },
    summary="Create project label",
    description=(
        "Versioned project label creation contract. Label persistence is intentionally "
        "deferred until the backing schema and data access stories."
    ),
)
def create_project_label(project_id: str, _request: ProjectLabelCreateRequest) -> JSONResponse:
    _ = project_id
    error = _labels_not_implemented_error()
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content=error.model_dump(),
    )


@router.get(
    "/{project_id}/components",
    response_model=ProjectComponentListResponse,
    responses={
        status.HTTP_501_NOT_IMPLEMENTED: {
            "model": ProjectApiErrorResponse,
            "description": "Project component listing is defined but not implemented yet.",
        },
    },
    summary="List project components",
    description=(
        "Versioned project component listing contract. Component persistence and retrieval are "
        "intentionally deferred until the backing schema and data access stories."
    ),
)
def list_project_components(project_id: str) -> JSONResponse:
    _ = project_id
    error = _components_not_implemented_error()
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content=error.model_dump(),
    )


@router.post(
    "/{project_id}/components",
    response_model=ProjectComponentResponse,
    responses={
        status.HTTP_501_NOT_IMPLEMENTED: {
            "model": ProjectApiErrorResponse,
            "description": "Project component creation is defined but not implemented yet.",
        },
    },
    summary="Create project component",
    description=(
        "Versioned project component creation contract. Component persistence is intentionally "
        "deferred until the backing schema and data access stories."
    ),
)
def create_project_component(
    project_id: str,
    _request: ProjectComponentCreateRequest,
) -> JSONResponse:
    _ = project_id
    error = _components_not_implemented_error()
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content=error.model_dump(),
    )


@router.get(
    "/{project_id}/versions",
    response_model=ProjectVersionListResponse,
    responses={
        status.HTTP_501_NOT_IMPLEMENTED: {
            "model": ProjectApiErrorResponse,
            "description": "Project version listing is defined but not implemented yet.",
        },
    },
    summary="List project versions",
    description=(
        "Versioned project version listing contract. Version persistence and retrieval are "
        "intentionally deferred until the backing schema and data access stories."
    ),
)
def list_project_versions(project_id: str) -> JSONResponse:
    _ = project_id
    error = _versions_not_implemented_error()
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content=error.model_dump(),
    )


@router.post(
    "/{project_id}/versions",
    response_model=ProjectVersionResponse,
    responses={
        status.HTTP_501_NOT_IMPLEMENTED: {
            "model": ProjectApiErrorResponse,
            "description": "Project version creation is defined but not implemented yet.",
        },
    },
    summary="Create project version",
    description=(
        "Versioned project version creation contract. Version persistence is intentionally "
        "deferred until the backing schema and data access stories."
    ),
)
def create_project_version(
    project_id: str,
    _request: ProjectVersionCreateRequest,
) -> JSONResponse:
    _ = project_id
    error = _versions_not_implemented_error()
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content=error.model_dump(),
    )
