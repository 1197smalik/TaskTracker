"""Project-domain API routes."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.projects.schemas import (
    ProjectApiErrorResponse,
    ProjectComponentCreateRequest,
    ProjectComponentListResponse,
    ProjectComponentResponse,
    ProjectLabelCreateRequest,
    ProjectLabelListResponse,
    ProjectLabelResponse,
    ProjectVersionCreateRequest,
    ProjectVersionListResponse,
    ProjectVersionResponse,
    ProjectWorkflowStateCatalogResponse,
    ProjectWorkflowStateResponse,
)
from taskmaster_backend.workflows.repository import (
    PROJECT_NOT_FOUND,
    WORKFLOW_ASSIGNMENT_NOT_FOUND,
    WORKFLOW_DEFINITION_NOT_FOUND,
    list_project_workflow_state_catalog,
)

router = APIRouter(prefix="/projects", tags=["projects"])


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
