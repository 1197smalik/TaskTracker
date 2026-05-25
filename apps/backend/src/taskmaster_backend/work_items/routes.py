"""Work Item domain API routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from taskmaster_backend.audit.service import (
    AuditLogWriteRequest,
    create_outbox_event,
    write_audit_log,
)
from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.identity.models import Workspace
from taskmaster_backend.work_items.repository import (
    create_work_item,
    get_project,
    get_project_work_item,
    list_project_work_items,
    transition_work_item,
    update_work_item,
    validate_parent_relationship,
)
from taskmaster_backend.work_items.schemas import (
    WorkflowTransitionRequest,
    WorkflowTransitionResponse,
    WorkItemApiErrorResponse,
    WorkItemCreateRequest,
    WorkItemListParams,
    WorkItemListResponse,
    WorkItemResponse,
    WorkItemUpdateRequest,
)
from taskmaster_backend.workflows.validator import (
    WorkflowTransitionValidationRequest,
    WorkflowTransitionValidationResult,
    validate_work_item_transition,
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


def _invalid_parent_error(reason: str) -> WorkItemApiErrorResponse:
    return WorkItemApiErrorResponse(
        error_code="invalid_work_item_parent",
        message="Work item parent relationship is invalid.",
        details={"reason": reason},
        correlation_id=str(uuid4()),
    )


def _invalid_transition_error(
    result: WorkflowTransitionValidationResult,
) -> WorkItemApiErrorResponse:
    details: dict[str, str] = {}
    if result.error_code is not None:
        details["reason"] = result.error_code
    if result.rule_type is not None:
        details["rule_type"] = result.rule_type

    return WorkItemApiErrorResponse(
        error_code="invalid_work_item_transition",
        message="Work item workflow transition is invalid.",
        details=details,
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
        "Workflow transitions, parent-child relationships, and assignment validation "
        "are handled by later stories."
    ),
)
def create_project_work_item(
    project_id: str,
    request: WorkItemCreateRequest,
    session: Session = Depends(get_db_session),
) -> WorkItemResponse | JSONResponse:
    project = get_project(session, project_id)
    if project is None:
        error = _project_not_found_error()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )

    parent_error = validate_parent_relationship(session, project_id, None, request.parent_id)
    if parent_error is not None:
        error = _invalid_parent_error(parent_error)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error.model_dump(),
        )

    workspace = session.get(Workspace, project.workspace_id)
    if workspace is None:
        error = _project_not_found_error()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )

    correlation_id = str(uuid4())
    now = datetime.now(timezone.utc)
    work_item = create_work_item(session, project_id, request, commit=False)
    write_audit_log(
        session,
        AuditLogWriteRequest(
            actor_type="system",
            organization_id=workspace.organization_id,
            workspace_id=workspace.id,
            project_id=project.id,
            entity_type="work_item",
            entity_id=work_item.id,
            action="work_item.created",
            after_summary={
                "type": work_item.type,
                "status": work_item.status,
                "title": work_item.title,
            },
            correlation_id=correlation_id,
        ),
        commit=False,
    )
    create_outbox_event(
        session,
        event_type="work_item.created",
        occurred_at=now,
        actor_id=None,
        organization_id=workspace.organization_id,
        workspace_id=workspace.id,
        project_id=project.id,
        entity_type="work_item",
        entity_id=work_item.id,
        correlation_id=correlation_id,
        payload={
            "type": work_item.type,
            "status": work_item.status,
            "title": work_item.title,
            "description": work_item.description,
        },
    )
    session.commit()
    session.refresh(work_item)
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
        status.HTTP_400_BAD_REQUEST: {
            "model": WorkItemApiErrorResponse,
            "description": "Parent relationship failed validation.",
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

    if "parent_id" in request.update_fields():
        parent_error = validate_parent_relationship(
            session,
            project_id,
            work_item_id,
            request.parent_id,
        )
        if parent_error is not None:
            error = _invalid_parent_error(parent_error)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error.model_dump(),
            )

    updated_work_item = update_work_item(session, work_item, request)
    return WorkItemResponse.from_model(updated_work_item)


@router.post(
    "/{work_item_id}/transition",
    response_model=WorkflowTransitionResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": WorkItemApiErrorResponse,
            "description": "Work item was not found or is inaccessible.",
        },
        status.HTTP_409_CONFLICT: {
            "model": WorkItemApiErrorResponse,
            "description": "Work item version does not match the expected version.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": WorkItemApiErrorResponse,
            "description": "Workflow transition failed validation.",
        },
    },
    summary="Transition work item",
    description=(
        "Validate and apply a project-scoped workflow transition to a work item. "
        "This updates the current workflow state, increments the work item version, "
        "and writes audit history. Event dispatch, automation, notifications, and "
        "activity feed records are handled by later stories."
    ),
)
def transition_project_work_item_route(
    project_id: str,
    work_item_id: str,
    request: WorkflowTransitionRequest,
    session: Session = Depends(get_db_session),
) -> WorkflowTransitionResponse | JSONResponse:
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

    validation_result = validate_work_item_transition(
        session,
        WorkflowTransitionValidationRequest(
            project_id=project_id,
            work_item_id=work_item_id,
            target_state_id=request.target_state_id,
            source_state_id=request.source_state_id,
        ),
    )
    if not validation_result.allowed or validation_result.transition_id is None:
        error = _invalid_transition_error(validation_result)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error.model_dump(),
        )

    project = get_project(session, project_id)
    if project is None:
        error = _project_not_found_error()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )

    workspace = session.get(Workspace, project.workspace_id)
    if workspace is None:
        error = _project_not_found_error()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )

    source_state_id = work_item.current_state_id
    updated_work_item = transition_work_item(
        session,
        work_item,
        request.target_state_id,
        commit=False,
    )
    write_audit_log(
        session,
        AuditLogWriteRequest(
            actor_type="system",
            organization_id=workspace.organization_id,
            workspace_id=workspace.id,
            project_id=project_id,
            entity_type="work_item",
            entity_id=updated_work_item.id,
            action="work_item.transitioned",
            before_summary={
                "source_state_id": source_state_id,
                "current_state_id": source_state_id,
            },
            after_summary={
                "target_state_id": request.target_state_id,
                "current_state_id": request.target_state_id,
            },
            correlation_id=str(uuid4()),
        ),
        commit=False,
    )
    session.commit()
    session.refresh(updated_work_item)

    return WorkflowTransitionResponse(
        work_item=WorkItemResponse.from_model(updated_work_item),
        transition_id=validation_result.transition_id,
        source_state_id=source_state_id or "",
        target_state_id=request.target_state_id,
    )
