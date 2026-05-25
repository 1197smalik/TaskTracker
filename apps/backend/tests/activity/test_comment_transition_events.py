"""Tests for activity events emitted by existing write paths."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.routing import APIRoute
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.activity.models import ActivityEvent
from taskmaster_backend.app import create_app
from taskmaster_backend.collaboration import routes as comment_routes
from taskmaster_backend.collaboration.models import Comment
from taskmaster_backend.collaboration.routes import create_work_item_comment
from taskmaster_backend.collaboration.schemas import CommentCreateRequest, CommentResponse
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal
from taskmaster_backend.identity.models import Organization, User, Workspace
from taskmaster_backend.identity.rbac import PermissionGrant, PermissionScope
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


def _seed_comment_scope(session_factory: sessionmaker[Session]) -> str:
    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        workspace = Workspace(id="workspace-1", organization_id="org-1", name="Platform")
        project = Project(id="project-1", workspace_id="workspace-1", key="TM", name="TaskMaster")
        user = User(
            id="user-123",
            email="user@example.com",
            password_hash="not-a-real-hash",
        )
        work_item = WorkItem(
            id="work-item-1",
            project_id="project-1",
            type="task",
            status="todo",
            title="Comment target",
        )
        session.add_all([organization, workspace, project, user, work_item])
        session.commit()
        return work_item.id


def _seed_transition_scope(session_factory: sessionmaker[Session]) -> dict[str, str]:
    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        workspace = Workspace(id="workspace-1", organization_id="org-1", name="Platform")
        project = Project(id="project-1", workspace_id="workspace-1", key="TM", name="TaskMaster")
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
        transition = WorkflowTransition(
            id="transition-1",
            workflow_definition_id="workflow-1",
            source_state_id="state-backlog",
            target_state_id="state-review",
        )
        assignment = WorkflowAssignment(
            id="assignment-1",
            project_id="project-1",
            workflow_definition_id="workflow-1",
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
        session.add_all(
            [
                organization,
                workspace,
                project,
                workflow,
                backlog,
                review,
                transition,
                assignment,
                work_item,
            ]
        )
        session.commit()
        return {
            "project_id": project.id,
            "work_item_id": work_item.id,
            "source_state_id": backlog.id,
            "target_state_id": review.id,
            "transition_id": transition.id,
        }


def test_comment_create_writes_activity_event_in_same_transaction() -> None:
    session_factory = _create_test_session_factory()
    work_item_id = _seed_comment_scope(session_factory)

    with session_factory() as session:
        response = create_work_item_comment(
            "project-1",
            work_item_id,
            CommentCreateRequest(body="Please review this, @Alice."),
            session,
            _principal(),
            _comment_create_grants(),
        )

    assert isinstance(response, CommentResponse)

    with session_factory() as session:
        comment = session.scalars(select(Comment)).one()
        activity_event = session.scalars(select(ActivityEvent)).one()

    assert activity_event.actor_id == "user-123"
    assert activity_event.project_id == "project-1"
    assert activity_event.entity_type == "comment"
    assert activity_event.entity_id == comment.id
    assert activity_event.event_type == "comment.created"
    assert activity_event.summary == "Comment added"
    assert activity_event.payload == {
        "comment_id": comment.id,
        "work_item_id": work_item_id,
        "mentioned_handles": ["alice"],
    }


def test_failed_comment_activity_write_rolls_back_comment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_test_session_factory()
    work_item_id = _seed_comment_scope(session_factory)

    def fail_activity_write(*args: Any, **kwargs: Any) -> ActivityEvent:
        raise RuntimeError("activity write failed")

    monkeypatch.setattr(comment_routes, "write_activity_event", fail_activity_write)

    with session_factory() as session:
        with pytest.raises(RuntimeError, match="activity write failed"):
            create_work_item_comment(
                "project-1",
                work_item_id,
                CommentCreateRequest(body="This should roll back."),
                session,
                _principal(),
                _comment_create_grants(),
            )

    with session_factory() as session:
        assert list(session.scalars(select(Comment))) == []
        assert list(session.scalars(select(ActivityEvent))) == []


def test_work_item_transition_writes_activity_event_in_same_transaction() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_transition_scope(session_factory)
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

    with session_factory() as session:
        activity_event = session.scalars(select(ActivityEvent)).one()

    assert activity_event.actor_id is None
    assert activity_event.project_id == ids["project_id"]
    assert activity_event.entity_type == "work_item"
    assert activity_event.entity_id == ids["work_item_id"]
    assert activity_event.event_type == "work_item.transitioned"
    assert activity_event.summary == "Work item transitioned"
    assert activity_event.payload == {
        "source_state_id": ids["source_state_id"],
        "target_state_id": ids["target_state_id"],
        "transition_id": ids["transition_id"],
    }


def test_activity_integration_does_not_add_activity_routes() -> None:
    app = create_app()
    activity_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute) and "/activity" in route.path
    ]

    assert activity_routes == []


def _principal() -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        subject="user-123",
        issuer="test-issuer",
        audience="test-audience",
        expires_at=9_999_999_999,
    )


def _comment_create_grants() -> list[PermissionGrant]:
    return [
        PermissionGrant(
            actor_id="user-123",
            permission="comment.create",
            scope=PermissionScope(scope_type="project", scope_id="project-1"),
        ),
    ]
