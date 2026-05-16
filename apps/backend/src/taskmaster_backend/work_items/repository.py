"""Persistence helpers for Work Item endpoints."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskmaster_backend.projects.models import Project
from taskmaster_backend.work_items.models import WorkItem
from taskmaster_backend.work_items.schemas import WorkItemCreateRequest


def get_project(session: Session, project_id: str) -> Project | None:
    return session.get(Project, project_id)


def create_work_item(
    session: Session,
    project_id: str,
    request: WorkItemCreateRequest,
) -> WorkItem:
    work_item = WorkItem(
        project_id=project_id,
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
