"""Project-domain API routes."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

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
