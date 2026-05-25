"""Tests for notification creation worker behavior."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.audit.models import EventOutbox
from taskmaster_backend.collaboration.events import COMMENT_MENTION_DETECTED_EVENT_TYPE
from taskmaster_backend.collaboration.models import Notification
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization, User, Workspace
from taskmaster_backend.notifications.service import create_notifications_from_event
from taskmaster_backend.notifications.worker import NotificationCreationWorker
from taskmaster_backend.projects.models import Project
from taskmaster_backend.workers.config import WorkerConfig


def _create_session_factory(tmp_path: Path) -> sessionmaker[Session]:
    engine = create_engine(
        f"sqlite+pysqlite:///{tmp_path / 'notifications.db'}",
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
                    id="recipient-1",
                    email="recipient-1@example.com",
                    password_hash="not-a-real-hash",
                ),
                User(
                    id="recipient-2",
                    email="recipient-2@example.com",
                    password_hash="not-a-real-hash",
                ),
            ]
        )
        session.commit()


def _add_event(
    session: Session,
    *,
    event_id: str = "event-1",
    event_type: str = COMMENT_MENTION_DETECTED_EVENT_TYPE,
    resolved_user_ids: list[object] | None = None,
) -> EventOutbox:
    event = EventOutbox(
        event_id=event_id,
        event_type=event_type,
        occurred_at=datetime.now(timezone.utc),
        actor_id="author-1",
        organization_id="org-1",
        workspace_id="workspace-1",
        project_id="project-1",
        entity_type="comment",
        entity_id="comment-1",
        correlation_id=f"correlation-{event_id}",
        payload={
            "comment_id": "comment-1",
            "work_item_id": "work-item-1",
            "project_id": "project-1",
            "author_id": "author-1",
            "mentioned_handles": ["owner"],
            "mention_recipient_resolution": {
                "strategy": "raw_handle_only",
                "unresolved_handles": ["owner"],
                "resolved_user_ids": resolved_user_ids or [],
            },
        },
    )
    session.add(event)
    return event


def test_unresolved_raw_handles_create_no_notifications(tmp_path: Path) -> None:
    session_factory = _create_session_factory(tmp_path)
    _seed_scope(session_factory)

    with session_factory() as session:
        event = _add_event(session)
        result = create_notifications_from_event(session, event)
        session.commit()

    with session_factory() as session:
        notifications = list(session.scalars(select(Notification)))

    assert result.created_count == 0
    assert result.reason == "no_resolved_recipients"
    assert notifications == []


def test_resolved_user_ids_create_notification_rows(tmp_path: Path) -> None:
    session_factory = _create_session_factory(tmp_path)
    _seed_scope(session_factory)

    with session_factory() as session:
        event = _add_event(session, resolved_user_ids=["recipient-1", "recipient-2"])
        result = create_notifications_from_event(session, event)
        session.commit()

    with session_factory() as session:
        notifications = list(
            session.scalars(select(Notification).order_by(Notification.recipient_id))
        )

    assert result.created_count == 2
    assert result.skipped_count == 0
    assert [notification.recipient_id for notification in notifications] == [
        "recipient-1",
        "recipient-2",
    ]
    assert {notification.notification_type for notification in notifications} == {
        "comment.mention",
    }
    assert {notification.entity_type for notification in notifications} == {"comment"}
    assert {notification.entity_id for notification in notifications} == {"comment-1"}
    assert {notification.payload["source_event_id"] for notification in notifications} == {
        "event-1",
    }


def test_duplicate_event_processing_does_not_create_duplicate_notifications(
    tmp_path: Path,
) -> None:
    session_factory = _create_session_factory(tmp_path)
    _seed_scope(session_factory)

    with session_factory() as session:
        event = _add_event(session, resolved_user_ids=["recipient-1"])
        first_result = create_notifications_from_event(session, event)
        second_result = create_notifications_from_event(session, event)
        session.commit()

    with session_factory() as session:
        notifications = list(session.scalars(select(Notification)))

    assert first_result.created_count == 1
    assert second_result.created_count == 0
    assert second_result.skipped_count == 1
    assert len(notifications) == 1


def test_malformed_or_unsupported_events_are_ignored_deterministically(
    tmp_path: Path,
) -> None:
    session_factory = _create_session_factory(tmp_path)
    _seed_scope(session_factory)

    with session_factory() as session:
        unsupported_event = _add_event(
            session,
            event_id="event-unsupported",
            event_type="comment.created",
            resolved_user_ids=["recipient-1"],
        )
        malformed_event = _add_event(
            session,
            event_id="event-malformed",
            resolved_user_ids=None,
        )
        malformed_event.payload = {"mentioned_handles": ["owner"]}
        unsupported_result = create_notifications_from_event(session, unsupported_event)
        malformed_result = create_notifications_from_event(session, malformed_event)
        session.commit()

    with session_factory() as session:
        notifications = list(session.scalars(select(Notification)))

    assert unsupported_result.reason == "unsupported_event_type"
    assert malformed_result.reason == "no_resolved_recipients"
    assert notifications == []


def test_no_user_handle_guessing_occurs(tmp_path: Path) -> None:
    session_factory = _create_session_factory(tmp_path)
    _seed_scope(session_factory)

    with session_factory() as session:
        event = _add_event(session, resolved_user_ids=[])
        event.payload["mention_recipient_resolution"] = {
            "strategy": "raw_handle_only",
            "unresolved_handles": ["recipient-1"],
            "resolved_user_ids": [],
        }
        result = create_notifications_from_event(session, event)
        session.commit()

    with session_factory() as session:
        notifications = list(session.scalars(select(Notification)))

    assert result.created_count == 0
    assert notifications == []


def test_notification_creation_worker_processes_supported_outbox_event(tmp_path: Path) -> None:
    session_factory = _create_session_factory(tmp_path)
    _seed_scope(session_factory)

    with session_factory() as session:
        event = _add_event(session, resolved_user_ids=["recipient-1"])
        session.commit()
        event_id = event.id

    worker = NotificationCreationWorker(
        WorkerConfig(name="notification-creation"),
        database_url=f"sqlite+pysqlite:///{tmp_path / 'notifications.db'}",
    )
    worker.initialize()

    assert worker.run_once() == 1

    with session_factory() as session:
        event = session.scalars(select(EventOutbox).filter_by(id=event_id)).one()
        notifications = list(session.scalars(select(Notification)))

    assert event.status == "dispatched"
    assert len(notifications) == 1
