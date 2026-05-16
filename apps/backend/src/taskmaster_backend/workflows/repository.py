"""Persistence helpers for workflow assignment behavior."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskmaster_backend.projects.models import Project
from taskmaster_backend.work_items.models import WorkItem
from taskmaster_backend.workflows.models import (
    WorkflowAssignment,
    WorkflowDefinition,
    WorkflowState,
    WorkflowTransition,
    WorkflowTransitionRule,
)

PROJECT_NOT_FOUND = "project_not_found"
WORKFLOW_DEFINITION_NOT_FOUND = "workflow_definition_not_found"


def get_project(session: Session, project_id: str) -> Project | None:
    return session.get(Project, project_id)


def get_project_workflow_definition(
    session: Session,
    project_id: str,
    workflow_definition_id: str,
) -> WorkflowDefinition | None:
    statement = select(WorkflowDefinition).where(
        WorkflowDefinition.project_id == project_id,
        WorkflowDefinition.id == workflow_definition_id,
    )
    return session.scalars(statement).one_or_none()


def get_project_workflow_assignment(
    session: Session,
    project_id: str,
) -> WorkflowAssignment | None:
    statement = select(WorkflowAssignment).where(
        WorkflowAssignment.project_id == project_id,
    )
    return session.scalars(statement).one_or_none()


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


def get_workflow_state(
    session: Session,
    workflow_definition_id: str,
    state_id: str,
) -> WorkflowState | None:
    statement = select(WorkflowState).where(
        WorkflowState.workflow_definition_id == workflow_definition_id,
        WorkflowState.id == state_id,
    )
    return session.scalars(statement).one_or_none()


def get_workflow_transition(
    session: Session,
    workflow_definition_id: str,
    source_state_id: str,
    target_state_id: str,
) -> WorkflowTransition | None:
    statement = select(WorkflowTransition).where(
        WorkflowTransition.workflow_definition_id == workflow_definition_id,
        WorkflowTransition.source_state_id == source_state_id,
        WorkflowTransition.target_state_id == target_state_id,
    )
    return session.scalars(statement).one_or_none()


def list_transition_rules(
    session: Session,
    workflow_transition_id: str,
) -> list[WorkflowTransitionRule]:
    statement = (
        select(WorkflowTransitionRule)
        .where(WorkflowTransitionRule.workflow_transition_id == workflow_transition_id)
        .order_by(WorkflowTransitionRule.rule_type.asc(), WorkflowTransitionRule.id.asc())
    )
    return list(session.scalars(statement).all())


def list_child_work_items(
    session: Session,
    project_id: str,
    parent_id: str,
) -> list[WorkItem]:
    statement = select(WorkItem).where(
        WorkItem.project_id == project_id,
        WorkItem.parent_id == parent_id,
    )
    return list(session.scalars(statement).all())


def assign_project_workflow(
    session: Session,
    project_id: str,
    workflow_definition_id: str,
) -> tuple[WorkflowAssignment | None, str | None]:
    if get_project(session, project_id) is None:
        return None, PROJECT_NOT_FOUND

    if (
        get_project_workflow_definition(session, project_id, workflow_definition_id)
        is None
    ):
        return None, WORKFLOW_DEFINITION_NOT_FOUND

    assignment = get_project_workflow_assignment(session, project_id)
    if assignment is None:
        assignment = WorkflowAssignment(
            project_id=project_id,
            workflow_definition_id=workflow_definition_id,
        )
    else:
        assignment.workflow_definition_id = workflow_definition_id

    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return assignment, None
