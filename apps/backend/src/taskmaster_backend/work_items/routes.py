"""Work Item domain API routes."""

from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.work_items.repository import (
    create_work_item,
    get_project,
    get_project_work_item,
    list_project_work_items,
    update_work_item,
)
from taskmaster_backend.work_items.schemas import (
    WorkItemApiErrorResponse,
    WorkItemCreateRequest,
    WorkItemListParams,
    WorkItemListResponse,
    WorkItemResponse,
    WorkItemUpdateRequest,
)

router = APIRouter(prefix="/projects/{project_id}/work-items", tags=["work-items"])


def _project_not_found_error() -> WorkItemApiErrorResponse:
    return WorkItemApiErrorResponse(
        error_code="project_not_found",
        message="Project was not found or is inaccessible.",
        correlation_id=str(uuid4()),
    )


def _work_item_not_found_error() -> WorkItemApiErrorResponse:
    return WorkItemApiErrorResponse(
        error_code="work_item_not_found",
        message="Work item was not found or is inaccessible.",
        correlation_id=str(uuid4()),
    )


def _work_item_version_conflict_error(current_version: int) -> WorkItemApiErrorResponse:
    return WorkItemApiErrorResponse(
        error_code="work_item_version_conflict",
        message="Work item version does not match the expected version.",
        details={"current_version": str(current_version)},
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


@router.get(
    "",
    response_model=WorkItemListResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": WorkItemApiErrorResponse,
            "description": "Project was not found or is inaccessible.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Pagination parameters failed validation.",
        },
    },
    summary="List work items",
    description=(
        "List project-scoped work items using deterministic offset pagination. "
        "Advanced filters, sorting, hierarchy, and workflow-aware views are handled "
        "by later stories."
    ),
)
def list_project_work_items_route(
    project_id: str,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: Session = Depends(get_db_session),
) -> WorkItemListResponse | JSONResponse:
    if get_project(session, project_id) is None:
        error = _project_not_found_error()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )

    pagination = WorkItemListParams(limit=limit, offset=offset)
    work_items, total = list_project_work_items(
        session,
        project_id,
        pagination.limit,
        pagination.offset,
    )
    return WorkItemListResponse(
        items=[WorkItemResponse.from_model(work_item) for work_item in work_items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get(
    "/{work_item_id}",
    response_model=WorkItemResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": WorkItemApiErrorResponse,
            "description": "Work item was not found or is inaccessible.",
        },
    },
    summary="Get work item detail",
    description=(
        "Fetch a single project-scoped work item by id. Cross-project access returns "
        "a stable not found response. Workflow, hierarchy, and related collections "
        "are handled by later stories."
    ),
)
def get_project_work_item_detail(
    project_id: str,
    work_item_id: str,
    session: Session = Depends(get_db_session),
) -> WorkItemResponse | JSONResponse:
    work_item = get_project_work_item(session, project_id, work_item_id)
    if work_item is None:
        error = _work_item_not_found_error()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )

    return WorkItemResponse.from_model(work_item)


@router.patch(
    "/{work_item_id}",
    response_model=WorkItemResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": WorkItemApiErrorResponse,
            "description": "Work item was not found or is inaccessible.",
        },
        status.HTTP_409_CONFLICT: {
            "model": WorkItemApiErrorResponse,
            "description": "Work item version does not match the expected version.",
        },
    },
    summary="Update work item",
    description=(
        "Update allowed fields on a project-scoped work item using optimistic "
        "version checking. Workflow state changes, hierarchy updates, and audit "
        "events are handled by later stories."
    ),
)
def update_project_work_item_route(
    project_id: str,
    work_item_id: str,
    request: WorkItemUpdateRequest,
    session: Session = Depends(get_db_session),
) -> WorkItemResponse | JSONResponse:
    work_item = get_project_work_item(session, project_id, work_item_id)
    if work_item is None:
        error = _work_item_not_found_error()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )

    if work_item.version != request.expected_version:
        error = _work_item_version_conflict_error(work_item.version)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=error.model_dump(),
        )

    updated_work_item = update_work_item(session, work_item, request)
    return WorkItemResponse.from_model(updated_work_item)
