"""Persistence helpers for workflow assignment behavior."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskmaster_backend.projects.models import Project
from taskmaster_backend.workflows.models import WorkflowAssignment, WorkflowDefinition

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
