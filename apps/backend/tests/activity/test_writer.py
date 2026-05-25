"""Tests for the activity writer service."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.activity.models import ActivityEvent
from taskmaster_backend.activity.service import (
    ActivityEventWriteRequest,
    write_activity_event,
)
from taskmaster_backend.audit.models import EventOutbox
from taskmaster_backend.collaboration.models import Notification
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization, User, Workspace
from taskmaster_backend.projects.models import Project


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def _seed_scope(session_factory: sessionmaker[Session]) -> dict[str, str]:
    with session_factory() as session:
        actor = User(
            id="user-1",
            email="user@example.com",
            password_hash="hashed",
        )
        organization = Organization(id="org-1", name="Acme")
        workspace = Workspace(id="workspace-1", organization_id="org-1", name="Platform")
        project = Project(
            id="project-1",
            workspace_id="workspace-1",
            key="TM",
            name="TaskMaster",
        )
        session.add_all([actor, organization, workspace, project])
        session.commit()
        return {
            "actor_id": actor.id,
            "project_id": project.id,
        }


def test_activity_writer_persists_activity_event_row() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_scope(session_factory)
    created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)

    with session_factory() as session:
        activity_event = write_activity_event(
            session,
            ActivityEventWriteRequest(
                actor_id=ids["actor_id"],
                project_id=ids["project_id"],
                entity_type="comment",
                entity_id="comment-1",
                event_type="comment.created",
                summary="Comment added",
                payload={"work_item_id": "work-item-1"},
                created_at=created_at,
            ),
        )

    assert activity_event.id != ""
    assert activity_event.actor_id == ids["actor_id"]
    assert activity_event.project_id == ids["project_id"]
    assert activity_event.entity_type == "comment"
    assert activity_event.entity_id == "comment-1"
    assert activity_event.event_type == "comment.created"
    assert activity_event.summary == "Comment added"
    assert activity_event.payload == {"work_item_id": "work-item-1"}

    with session_factory() as session:
        persisted = session.scalars(select(ActivityEvent)).one()

    assert persisted.id == activity_event.id
    assert persisted.created_at.replace(tzinfo=timezone.utc) == created_at


def test_activity_writer_requires_non_empty_required_fields() -> None:
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        with pytest.raises(ValueError, match="entity_type is required"):
            write_activity_event(
                session,
                ActivityEventWriteRequest(
                    entity_type=" ",
                    entity_id="comment-1",
                    event_type="comment.created",
                ),
            )

        with pytest.raises(ValueError, match="entity_id is required"):
            write_activity_event(
                session,
                ActivityEventWriteRequest(
                    entity_type="comment",
                    entity_id="",
                    event_type="comment.created",
                ),
            )

        with pytest.raises(ValueError, match="event_type is required"):
            write_activity_event(
                session,
                ActivityEventWriteRequest(
                    entity_type="comment",
                    entity_id="comment-1",
                    event_type=" ",
                ),
            )


def test_activity_writer_rejects_empty_optional_scope_values() -> None:
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        with pytest.raises(ValueError, match="actor_id cannot be empty"):
            write_activity_event(
                session,
                ActivityEventWriteRequest(
                    actor_id=" ",
                    entity_type="comment",
                    entity_id="comment-1",
                    event_type="comment.created",
                ),
            )

        with pytest.raises(ValueError, match="summary cannot be empty"):
            write_activity_event(
                session,
                ActivityEventWriteRequest(
                    entity_type="comment",
                    entity_id="comment-1",
                    event_type="comment.created",
                    summary=" ",
                ),
            )


def test_activity_writer_can_participate_in_caller_transaction() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        activity_event = write_activity_event(
            session,
            ActivityEventWriteRequest(
                entity_type="work_item",
                entity_id="work-item-1",
                event_type="work_item.transitioned",
            ),
            commit=False,
        )
        assert activity_event.id != ""
        session.rollback()

    with session_factory() as session:
        assert list(session.scalars(select(ActivityEvent))) == []


def test_activity_writer_is_append_only() -> None:
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        first = write_activity_event(
            session,
            ActivityEventWriteRequest(
                entity_type="comment",
                entity_id="comment-1",
                event_type="comment.created",
            ),
        )
        second = write_activity_event(
            session,
            ActivityEventWriteRequest(
                entity_type="comment",
                entity_id="comment-1",
                event_type="comment.updated",
            ),
        )

    assert first.id != second.id

    with session_factory() as session:
        persisted = list(
            session.scalars(
                select(ActivityEvent).order_by(ActivityEvent.created_at.asc())
            )
        )

    assert len(persisted) == 2
    assert [item.event_type for item in persisted] == [
        "comment.created",
        "comment.updated",
    ]


def test_activity_writer_does_not_create_notifications_or_outbox_events() -> None:
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        write_activity_event(
            session,
            ActivityEventWriteRequest(
                entity_type="comment",
                entity_id="comment-1",
                event_type="comment.created",
            ),
        )

    with session_factory() as session:
        assert list(session.scalars(select(Notification))) == []
        assert list(session.scalars(select(EventOutbox))) == []
