"""Tests for audit logging during WorkItem workflow transitions."""

from __future__ import annotations

from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.audit.models import AuditLog
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization, Workspace
from taskmaster_backend.projects.models import Project
from taskmaster_backend.work_items.models import WorkItem
from taskmaster_backend.work_items.routes import transition_project_work_item_route
from taskmaster_backend.work_items.schemas import (
    WorkflowTransitionRequest,
    WorkflowTransitionResponse,
)
from taskmaster_backend.workflows.models import (
    WorkflowAssignment,
    WorkflowDefinition,
    WorkflowState,
    WorkflowTransition,
)


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def _seed_work_items_and_workflow(
    session_factory: sessionmaker[Session],
    *,
    with_assignment: bool = True,
) -> dict[str, str]:
    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        workspace = Workspace(id="workspace-1", organization_id="org-1", name="Platform")
        project = Project(
            id="project-1",
            workspace_id="workspace-1",
            key="TM",
            name="TaskMaster",
        )
        workflow = WorkflowDefinition(
            id="workflow-1",
            project_id="project-1",
            name="Default",
            version=1,
        )
        backlog = WorkflowState(
            id="state-backlog",
            workflow_definition_id="workflow-1",
            name="Backlog",
        )
        review = WorkflowState(
            id="state-review",
            workflow_definition_id="workflow-1",
            name="Review",
        )
        done = WorkflowState(
            id="state-done",
            workflow_definition_id="workflow-1",
            name="Done",
        )
        transition = WorkflowTransition(
            id="transition-1",
            workflow_definition_id="workflow-1",
            source_state_id="state-backlog",
            target_state_id="state-review",
        )
        work_item = WorkItem(
            id="work-item-1",
            project_id="project-1",
            current_state_id="state-backlog",
            type="task",
            status="todo",
            title="Transition me",
            typed_metadata={},
            version=1,
        )
        records: list[object] = [
            organization,
            workspace,
            project,
            workflow,
            backlog,
            review,
            done,
            transition,
            work_item,
        ]
        if with_assignment:
            records.append(
                WorkflowAssignment(
                    id="assignment-1",
                    project_id="project-1",
                    workflow_definition_id="workflow-1",
                )
            )

        session.add_all(records)
        session.commit()
        return {
            "organization_id": organization.id,
            "workspace_id": workspace.id,
            "project_id": project.id,
            "work_item_id": work_item.id,
            "source_state_id": backlog.id,
            "target_state_id": review.id,
            "missing_transition_target_state_id": done.id,
            "transition_id": transition.id,
        }


def test_work_item_transition_writes_one_audit_log_with_transition_metadata() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_work_items_and_workflow(session_factory)
    request = WorkflowTransitionRequest(
        expected_version=1,
        source_state_id=ids["source_state_id"],
        target_state_id=ids["target_state_id"],
    )

    with session_factory() as session:
        response = transition_project_work_item_route(
            ids["project_id"],
            ids["work_item_id"],
            request,
            session,
        )

    assert isinstance(response, WorkflowTransitionResponse)
    assert response.transition_id == ids["transition_id"]
    assert response.source_state_id == ids["source_state_id"]
    assert response.target_state_id == ids["target_state_id"]
    assert response.work_item.id == ids["work_item_id"]
    assert response.work_item.current_state_id == ids["target_state_id"]
    assert response.work_item.version == 2

    with session_factory() as session:
        audit_logs = list(session.scalars(select(AuditLog)).all())

    assert len(audit_logs) == 1
    audit_log = audit_logs[0]
    assert audit_log.entity_type == "work_item"
    assert audit_log.entity_id == ids["work_item_id"]
    assert audit_log.action == "work_item.transitioned"
    assert audit_log.organization_id == ids["organization_id"]
    assert audit_log.workspace_id == ids["workspace_id"]
    assert audit_log.project_id == ids["project_id"]
    assert audit_log.actor_id is None
    assert audit_log.actor_type == "system"
    assert audit_log.before_summary == {
        "source_state_id": ids["source_state_id"],
        "current_state_id": ids["source_state_id"],
    }
    assert audit_log.after_summary == {
        "target_state_id": ids["target_state_id"],
        "current_state_id": ids["target_state_id"],
    }
    assert audit_log.correlation_id != ""


def test_work_item_transition_missing_assignment_writes_no_audit_log() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_work_items_and_workflow(session_factory, with_assignment=False)
    request = WorkflowTransitionRequest(
        expected_version=1,
        target_state_id=ids["target_state_id"],
    )

    with session_factory() as session:
        response = transition_project_work_item_route(
            ids["project_id"],
            ids["work_item_id"],
            request,
            session,
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400

    with session_factory() as session:
        assert list(session.scalars(select(AuditLog)).all()) == []


def test_work_item_transition_stale_version_writes_no_audit_log() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_work_items_and_workflow(session_factory)
    request = WorkflowTransitionRequest(
        expected_version=2,
        target_state_id=ids["target_state_id"],
    )

    with session_factory() as session:
        response = transition_project_work_item_route(
            ids["project_id"],
            ids["work_item_id"],
            request,
            session,
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 409

    with session_factory() as session:
        assert list(session.scalars(select(AuditLog)).all()) == []


def test_work_item_transition_invalid_transition_writes_no_audit_log() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_work_items_and_workflow(session_factory)
    request = WorkflowTransitionRequest(
        expected_version=1,
        target_state_id=ids["missing_transition_target_state_id"],
    )

    with session_factory() as session:
        response = transition_project_work_item_route(
            ids["project_id"],
            ids["work_item_id"],
            request,
            session,
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400

    with session_factory() as session:
        assert list(session.scalars(select(AuditLog)).all()) == []
