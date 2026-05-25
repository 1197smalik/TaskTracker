"""Tests for notification list/read endpoint behavior."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.app import create_app
from taskmaster_backend.collaboration.models import Notification
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal
from taskmaster_backend.identity.models import Organization, User, Workspace
from taskmaster_backend.notifications.routes import list_notifications, mark_notification_read
from taskmaster_backend.notifications.schemas import NotificationListResponse, NotificationResponse
from taskmaster_backend.projects.models import Project


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def _seed_scope(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        session.add_all(
            [
                Organization(id="org-1", name="Acme"),
                Workspace(id="workspace-1", organization_id="org-1", name="Platform"),
                Project(id="project-1", workspace_id="workspace-1", key="TM", name="TaskMaster"),
                User(
                    id="user-123",
                    email="user-123@example.com",
                    password_hash="not-a-real-hash",
                ),
                User(
                    id="user-456",
                    email="user-456@example.com",
                    password_hash="not-a-real-hash",
                ),
            ]
        )
        session.commit()


def _add_notification(
    session: Session,
    *,
    notification_id: str,
    recipient_id: str,
    created_at: datetime,
    read_at: datetime | None = None,
) -> Notification:
    notification = Notification(
        id=notification_id,
        recipient_id=recipient_id,
        organization_id="org-1",
        workspace_id="workspace-1",
        project_id="project-1",
        notification_type="comment.mention",
        title=f"Notification {notification_id}",
        body=None,
        entity_type="comment",
        entity_id=f"comment-{notification_id}",
        payload={"source_event_id": f"event-{notification_id}"},
        read_at=read_at,
        created_at=created_at,
    )
    session.add(notification)
    return notification


def test_notification_routes_are_registered_under_versioned_api() -> None:
    app = create_app()
    notification_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute) and "/notifications" in route.path
    ]

    methods_by_path = {
        route.path: {method for method in route.methods}
        for route in notification_routes
    }

    assert methods_by_path["/api/v1/notifications"] == {"GET"}
    assert methods_by_path["/api/v1/notifications/{notification_id}/read"] == {"POST"}
    assert len(notification_routes) == 2


def test_list_notifications_scopes_to_authenticated_recipient() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)
    now = datetime.now(timezone.utc)
    with session_factory() as session:
        _add_notification(
            session,
            notification_id="notification-1",
            recipient_id="user-123",
            created_at=now,
        )
        _add_notification(
            session,
            notification_id="notification-2",
            recipient_id="user-456",
            created_at=now + timedelta(seconds=1),
        )
        session.commit()

    with session_factory() as session:
        response = list_notifications(
            limit=50,
            offset=0,
            session=session,
            principal=_principal("user-123"),
        )

    assert isinstance(response, NotificationListResponse)
    assert response.total == 1
    assert [item.id for item in response.items] == ["notification-1"]
    assert response.items[0].recipient_id == "user-123"


def test_list_notifications_reports_unread_and_read_state() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)
    now = datetime.now(timezone.utc)
    read_at = now + timedelta(minutes=1)
    with session_factory() as session:
        _add_notification(
            session,
            notification_id="unread",
            recipient_id="user-123",
            created_at=now,
        )
        _add_notification(
            session,
            notification_id="read",
            recipient_id="user-123",
            created_at=now + timedelta(seconds=1),
            read_at=read_at,
        )
        session.commit()

    with session_factory() as session:
        response = list_notifications(
            limit=50,
            offset=0,
            session=session,
            principal=_principal("user-123"),
        )

    states = {item.id: item for item in response.items}
    assert states["unread"].is_read is False
    assert states["unread"].read_at is None
    assert states["read"].is_read is True
    assert states["read"].read_at is not None


def test_list_notifications_applies_pagination() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)
    now = datetime.now(timezone.utc)
    with session_factory() as session:
        for index in range(3):
            _add_notification(
                session,
                notification_id=f"notification-{index}",
                recipient_id="user-123",
                created_at=now + timedelta(seconds=index),
            )
        session.commit()

    with session_factory() as session:
        response = list_notifications(
            limit=1,
            offset=1,
            session=session,
            principal=_principal("user-123"),
        )

    assert response.total == 3
    assert response.limit == 1
    assert response.offset == 1
    assert [item.id for item in response.items] == ["notification-1"]


def test_mark_notification_read_sets_read_timestamp() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)
    with session_factory() as session:
        _add_notification(
            session,
            notification_id="notification-1",
            recipient_id="user-123",
            created_at=datetime.now(timezone.utc),
        )
        session.commit()

    with session_factory() as session:
        response = mark_notification_read(
            "notification-1",
            session=session,
            principal=_principal("user-123"),
        )

    assert isinstance(response, NotificationResponse)
    assert response.id == "notification-1"
    assert response.is_read is True
    assert response.read_at is not None

    with session_factory() as session:
        notification = session.scalars(
            select(Notification).filter_by(id="notification-1")
        ).one()
        assert notification.read_at is not None


def test_cannot_mark_another_users_notification_read() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)
    with session_factory() as session:
        _add_notification(
            session,
            notification_id="notification-1",
            recipient_id="user-456",
            created_at=datetime.now(timezone.utc),
        )
        session.commit()

    with session_factory() as session:
        response = mark_notification_read(
            "notification-1",
            session=session,
            principal=_principal("user-123"),
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert b"notification_not_found" in response.body

    with session_factory() as session:
        notification = session.scalars(
            select(Notification).filter_by(id="notification-1")
        ).one()
        assert notification.read_at is None


def test_missing_notification_returns_stable_404() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        response = mark_notification_read(
            "missing-notification",
            session=session,
            principal=_principal("user-123"),
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert b"notification_not_found" in response.body


def _principal(subject: str) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        subject=subject,
        issuer="test-issuer",
        audience="test-audience",
        expires_at=9_999_999_999,
    )
