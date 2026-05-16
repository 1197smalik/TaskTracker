"""Work Item domain API routes."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.work_items.repository import create_work_item, get_project
from taskmaster_backend.work_items.schemas import (
    WorkItemApiErrorResponse,
    WorkItemCreateRequest,
    WorkItemResponse,
)

router = APIRouter(prefix="/projects/{project_id}/work-items", tags=["work-items"])


def _project_not_found_error() -> WorkItemApiErrorResponse:
    return WorkItemApiErrorResponse(
        error_code="project_not_found",
        message="Project was not found or is inaccessible.",
        correlation_id=str(uuid4()),
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=WorkItemResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": WorkItemApiErrorResponse,
            "description": "Project was not found or is inaccessible.",
        },
    },
    summary="Create work item",
    description=(
        "Create a project-scoped work item using the generic Work Item model. "
        "Workflow transitions, parent-child relationships, assignments validation, "
        "and audit events are handled by later stories."
    ),
)
def create_project_work_item(
    project_id: str,
    request: WorkItemCreateRequest,
    session: Session = Depends(get_db_session),
) -> WorkItemResponse | JSONResponse:
    if get_project(session, project_id) is None:
        error = _project_not_found_error()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )

    work_item = create_work_item(session, project_id, request)
    return WorkItemResponse.from_model(work_item)
