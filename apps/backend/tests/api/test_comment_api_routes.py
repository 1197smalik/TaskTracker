"""Tests for comment creation endpoint behavior."""

from __future__ import annotations

from typing import Any, cast

import pytest
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.app import create_app
from taskmaster_backend.audit.models import EventOutbox
from taskmaster_backend.collaboration import routes as comment_routes
from taskmaster_backend.collaboration.events import (
    COMMENT_CREATED_EVENT_TYPE,
    COMMENT_MENTION_DETECTED_EVENT_TYPE,
)
from taskmaster_backend.collaboration.models import Comment, Notification
from taskmaster_backend.collaboration.routes import create_work_item_comment
from taskmaster_backend.collaboration.schemas import CommentCreateRequest, CommentResponse
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal
from taskmaster_backend.identity.models import Organization, User, Workspace
from taskmaster_backend.identity.rbac import PermissionGrant, PermissionScope
from taskmaster_backend.projects.models import Project
from taskmaster_backend.work_items.models import WorkItem


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def _seed_work_item(session_factory: sessionmaker[Session]) -> str:
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


def test_comment_create_route_is_registered_under_versioned_api() -> None:
    app = create_app()
    routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path == "/api/v1/projects/{project_id}/work-items/{work_item_id}/comments"
    ]

    assert len(routes) == 1
    assert routes[0].methods == {"POST"}


def test_comment_create_route_openapi_contract_is_exposed() -> None:
    app = create_app()
    openapi_schema = app.openapi()
    path_item = openapi_schema["paths"][
        "/api/v1/projects/{project_id}/work-items/{work_item_id}/comments"
    ]["post"]

    assert path_item["summary"] == "Create work item comment"
    assert "requestBody" in path_item
    assert "201" in path_item["responses"]
    assert "401" in path_item["responses"]
    assert "403" in path_item["responses"]
    assert "404" in path_item["responses"]
    assert "422" in path_item["responses"]

    components = openapi_schema["components"]["schemas"]
    assert "CommentCreateRequest" in components
    assert "CommentResponse" in components
    assert "CommentApiErrorResponse" in components
    assert components["CommentCreateRequest"]["required"] == ["body"]


def test_comment_create_persists_row_and_emits_comment_created_event() -> None:
    session_factory = _create_test_session_factory()
    work_item_id = _seed_work_item(session_factory)
    request = CommentCreateRequest(body="This needs follow-up.")

    with session_factory() as session:
        response = create_work_item_comment(
            "project-1",
            work_item_id,
            request,
            session,
            _principal(),
            _comment_create_grants(),
        )

    assert isinstance(response, CommentResponse)
    assert response.work_item_id == work_item_id
    assert response.author_id == "user-123"
    assert response.body == "This needs follow-up."
    assert response.created_at
    assert response.updated_at

    with session_factory() as session:
        comment = session.scalars(select(Comment)).one()
        event = session.scalars(
            select(EventOutbox).filter_by(event_type=COMMENT_CREATED_EVENT_TYPE)
        ).one()
        assert comment.id == response.id
        assert comment.work_item_id == work_item_id
        assert comment.author_id == "user-123"
        assert event.entity_type == "comment"
        assert event.entity_id == comment.id
        assert event.actor_id == "user-123"
        assert event.organization_id == "org-1"
        assert event.workspace_id == "workspace-1"
        assert event.project_id == "project-1"
        assert event.payload_version == "1.0"
        assert event.payload["comment_id"] == comment.id
        assert event.payload["work_item_id"] == work_item_id
        assert event.payload["mentioned_handles"] == []
        assert session.scalars(select(Notification)).all() == []


def test_comment_create_includes_raw_mentions_without_resolved_users() -> None:
    session_factory = _create_test_session_factory()
    work_item_id = _seed_work_item(session_factory)
    request = CommentCreateRequest(body="Please check this, @Alice and @bob.")

    with session_factory() as session:
        response = create_work_item_comment(
            "project-1",
            work_item_id,
            request,
            session,
            _principal(),
            _comment_create_grants(),
        )

    assert isinstance(response, CommentResponse)

    with session_factory() as session:
        events = list(session.scalars(select(EventOutbox).order_by(EventOutbox.event_type)))
        events_by_type = {event.event_type: event for event in events}

    assert set(events_by_type) == {
        COMMENT_CREATED_EVENT_TYPE,
        COMMENT_MENTION_DETECTED_EVENT_TYPE,
    }
    comment_created = events_by_type[COMMENT_CREATED_EVENT_TYPE]
    mention_detected = events_by_type[COMMENT_MENTION_DETECTED_EVENT_TYPE]
    for event in (comment_created, mention_detected):
        assert event.payload["mentioned_handles"] == ["alice", "bob"]
        assert "mentioned_user_ids" not in event.payload
        assert "recipient_ids" not in event.payload
        resolution = event.payload["mention_recipient_resolution"]
        assert isinstance(resolution, dict)
        assert resolution == {
            "strategy": "raw_handle_only",
            "unresolved_handles": ["alice", "bob"],
            "resolved_user_ids": [],
        }

    with session_factory() as session:
        assert session.scalars(select(Notification)).all() == []


def test_failed_comment_create_emits_no_outbox_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_test_session_factory()
    work_item_id = _seed_work_item(session_factory)
    request = CommentCreateRequest(body="This transaction should roll back.")

    def fail_outbox(*args: object, **kwargs: object) -> EventOutbox:
        raise RuntimeError("outbox write failed")

    monkeypatch.setattr(comment_routes, "create_outbox_event", fail_outbox)

    with session_factory() as session:
        with pytest.raises(RuntimeError, match="outbox write failed"):
            create_work_item_comment(
                "project-1",
                work_item_id,
                request,
                session,
                _principal(),
                _comment_create_grants(),
            )

    with session_factory() as session:
        assert session.scalars(select(Comment)).all() == []
        assert session.scalars(select(EventOutbox)).all() == []
        assert session.scalars(select(Notification)).all() == []


def test_comment_create_validates_required_body() -> None:
    with pytest.raises(ValidationError):
        CommentCreateRequest.model_validate({})


def test_comment_create_rejects_blank_body() -> None:
    with pytest.raises(ValidationError):
        CommentCreateRequest(body="   ")


def test_comment_create_returns_not_found_for_unknown_work_item() -> None:
    session_factory = _create_test_session_factory()
    _seed_work_item(session_factory)
    request = CommentCreateRequest(body="Unknown target.")

    with session_factory() as session:
        response = create_work_item_comment(
            "project-1",
            "missing-work-item",
            request,
            session,
            _principal(),
            _comment_create_grants(),
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert b"work_item_not_found" in response.body


def test_comment_create_denies_missing_permission() -> None:
    session_factory = _create_test_session_factory()
    work_item_id = _seed_work_item(session_factory)
    request = CommentCreateRequest(body="Permission denied.")

    with session_factory() as session:
        with pytest.raises(HTTPException) as exc_info:
            create_work_item_comment(
                "project-1",
                work_item_id,
                request,
                session,
                _principal(),
                grants=[],
            )

    assert exc_info.value.status_code == 403
    detail = cast(dict[str, Any], exc_info.value.detail)
    assert detail["error_code"] == "permission_denied"


def test_comment_create_does_not_add_future_collaboration_routes() -> None:
    app = create_app()
    collaboration_routes = {
        (route.path, tuple(sorted(route.methods)))
        for route in app.routes
        if isinstance(route, APIRoute)
        and (
            "/comments" in route.path
            or "/mentions" in route.path
            or "/notifications" in route.path
            or "/activity" in route.path
        )
    }

    assert collaboration_routes == {
        (
            "/api/v1/projects/{project_id}/work-items/{work_item_id}/comments",
            ("POST",),
        ),
        ("/api/v1/notifications", ("GET",)),
        ("/api/v1/notifications/{notification_id}/read", ("POST",)),
    }


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
