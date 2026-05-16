"""Project-domain API routes."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from taskmaster_backend.projects.schemas import (
    ProjectApiErrorResponse,
    ProjectLabelCreateRequest,
    ProjectLabelListResponse,
    ProjectLabelResponse,
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
