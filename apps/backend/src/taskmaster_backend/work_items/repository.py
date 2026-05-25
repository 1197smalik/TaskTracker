"""Persistence helpers for Work Item endpoints."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from taskmaster_backend.projects.models import Project
from taskmaster_backend.work_items.models import WorkItem
from taskmaster_backend.work_items.schemas import WorkItemCreateRequest, WorkItemUpdateRequest


def get_project(session: Session, project_id: str) -> Project | None:
    return session.get(Project, project_id)


def create_work_item(
    session: Session,
    project_id: str,
    request: WorkItemCreateRequest,
    *,
    commit: bool = True,
) -> WorkItem:
    work_item = WorkItem(
        project_id=project_id,
        parent_id=request.parent_id,
        sprint_id=request.sprint_id,
        epic_id=request.epic_id,
        assignee_id=request.assignee_id,
        reporter_id=request.reporter_id,
        current_state_id=request.current_state_id,
        type=request.type,
        status=request.status,
        title=request.title,
        description=request.description,
        priority=request.priority,
        severity=request.severity,
        estimate=request.estimate,
        typed_metadata=request.typed_metadata,
    )
    session.add(work_item)
    session.flush()

    if commit:
        session.commit()
        session.refresh(work_item)

    return work_item


def get_project_work_item(
    session: Session,
    project_id: str,
    work_item_id: str,
) -> WorkItem | None:
    statement = select(WorkItem).where(
        WorkItem.project_id == project_id,
        WorkItem.id == work_item_id,
    )
    return session.scalars(statement).one_or_none()


def list_project_work_items(
    session: Session,
    project_id: str,
    limit: int,
    offset: int,
) -> tuple[list[WorkItem], int]:
    total = session.scalar(
        select(func.count()).select_from(WorkItem).where(WorkItem.project_id == project_id)
    )
    statement = (
        select(WorkItem)
        .where(WorkItem.project_id == project_id)
        .order_by(WorkItem.created_at.asc(), WorkItem.id.asc())
        .limit(limit)
        .offset(offset)
    )
    items = list(session.scalars(statement).all())
    return items, total or 0


def validate_parent_relationship(
    session: Session,
    project_id: str,
    work_item_id: str | None,
    parent_id: str | None,
) -> str | None:
    if parent_id is None:
        return None

    if work_item_id is not None and parent_id == work_item_id:
        return "self_parent"

    parent = get_project_work_item(session, project_id, parent_id)
    if parent is None:
        return "parent_not_found"

    if work_item_id is None:
        return None

    visited_parent_ids: set[str] = set()
    current_parent = parent
    while current_parent.parent_id is not None:
        if current_parent.parent_id == work_item_id:
            return "cycle"
        if current_parent.parent_id in visited_parent_ids:
            return "cycle"

        visited_parent_ids.add(current_parent.parent_id)
        next_parent = get_project_work_item(session, project_id, current_parent.parent_id)
        if next_parent is None:
            return None
        current_parent = next_parent

    return None


def update_work_item(
    session: Session,
    work_item: WorkItem,
    request: WorkItemUpdateRequest,
) -> WorkItem:
    for field_name, value in request.update_fields().items():
        setattr(work_item, field_name, value)

    work_item.version += 1
    session.add(work_item)
    session.commit()
    session.refresh(work_item)
    return work_item


def transition_work_item(
    session: Session,
    work_item: WorkItem,
    target_state_id: str,
    *,
    commit: bool = True,
) -> WorkItem:
    work_item.current_state_id = target_state_id
    work_item.version += 1
    session.add(work_item)

    if commit:
        session.commit()
        session.refresh(work_item)

    return work_item
