"""Tests for event outbox creation service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.audit.models import EventOutbox
from taskmaster_backend.audit.service import create_outbox_event
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def test_create_outbox_event_minimal() -> None:
    """Test creating an outbox event with minimal required fields."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        session.add(organization)
        session.commit()

        now = datetime.now(timezone.utc)
        event = create_outbox_event(
            session=session,
            event_type="work_item.created",
            occurred_at=now,
            actor_id=None,
            organization_id="org-1",
            workspace_id=None,
            project_id=None,
            entity_type="work_item",
            entity_id="work-1",
            correlation_id="corr-1",
            payload={"title": "New Task"},
        )
        session.commit()

        result = session.scalars(select(EventOutbox).filter_by(id=event.id)).first()
        assert result is not None
        assert result.event_type == "work_item.created"
        assert result.status == "pending"
        assert result.retry_count == 0
        assert result.payload["title"] == "New Task"


def test_create_outbox_event_with_all_fields() -> None:
    """Test creating an outbox event with all optional fields."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        session.add(organization)
        session.commit()

        now = datetime.now(timezone.utc)
        event = create_outbox_event(
            session=session,
            event_type="work_item.created",
            occurred_at=now,
            actor_id="user-1",
            organization_id="org-1",
            workspace_id="ws-1",
            project_id="proj-1",
            entity_type="work_item",
            entity_id="work-1",
            correlation_id="corr-1",
            payload={
                "type": "task",
                "title": "New Task",
                "description": "Task description",
            },
            payload_version="1.0",
        )
        session.commit()

        result = session.scalars(select(EventOutbox).filter_by(id=event.id)).first()
        assert result is not None
        assert result.actor_id == "user-1"
        assert result.workspace_id == "ws-1"
        assert result.project_id == "proj-1"
        assert result.payload_version == "1.0"


def test_create_outbox_event_generates_unique_event_ids() -> None:
    """Test that multiple events get unique event IDs."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        session.add(organization)
        session.commit()

        now = datetime.now(timezone.utc)

        event1 = create_outbox_event(
            session=session,
            event_type="work_item.created",
            occurred_at=now,
            actor_id=None,
            organization_id="org-1",
            workspace_id=None,
            project_id=None,
            entity_type="work_item",
            entity_id="work-1",
            correlation_id="corr-1",
            payload={"title": "Task 1"},
        )

        event2 = create_outbox_event(
            session=session,
            event_type="work_item.created",
            occurred_at=now,
            actor_id=None,
            organization_id="org-1",
            workspace_id=None,
            project_id=None,
            entity_type="work_item",
            entity_id="work-2",
            correlation_id="corr-2",
            payload={"title": "Task 2"},
        )

        session.commit()

        assert event1.event_id != event2.event_id


def test_create_outbox_event_missing_event_type() -> None:
    """Test validation of required event_type field."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        session.add(organization)
        session.commit()

        now = datetime.now(timezone.utc)
        try:
            create_outbox_event(
                session=session,
                event_type="",
                occurred_at=now,
                actor_id=None,
                organization_id="org-1",
                workspace_id=None,
                project_id=None,
                entity_type="work_item",
                entity_id="work-1",
                correlation_id="corr-1",
                payload={"title": "Task"},
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "event_type" in str(e)


def test_create_outbox_event_missing_organization_id() -> None:
    """Test validation of required organization_id field."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        now = datetime.now(timezone.utc)
        try:
            create_outbox_event(
                session=session,
                event_type="work_item.created",
                occurred_at=now,
                actor_id=None,
                organization_id="",
                workspace_id=None,
                project_id=None,
                entity_type="work_item",
                entity_id="work-1",
                correlation_id="corr-1",
                payload={"title": "Task"},
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "organization_id" in str(e)


def test_create_outbox_event_missing_entity_type() -> None:
    """Test validation of required entity_type field."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        session.add(organization)
        session.commit()

        now = datetime.now(timezone.utc)
        try:
            create_outbox_event(
                session=session,
                event_type="work_item.created",
                occurred_at=now,
                actor_id=None,
                organization_id="org-1",
                workspace_id=None,
                project_id=None,
                entity_type="",
                entity_id="work-1",
                correlation_id="corr-1",
                payload={"title": "Task"},
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "entity_type" in str(e)


def test_create_outbox_event_missing_entity_id() -> None:
    """Test validation of required entity_id field."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        session.add(organization)
        session.commit()

        now = datetime.now(timezone.utc)
        try:
            create_outbox_event(
                session=session,
                event_type="work_item.created",
                occurred_at=now,
                actor_id=None,
                organization_id="org-1",
                workspace_id=None,
                project_id=None,
                entity_type="work_item",
                entity_id="",
                correlation_id="corr-1",
                payload={"title": "Task"},
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "entity_id" in str(e)


def test_create_outbox_event_missing_correlation_id() -> None:
    """Test validation of required correlation_id field."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        session.add(organization)
        session.commit()

        now = datetime.now(timezone.utc)
        try:
            create_outbox_event(
                session=session,
                event_type="work_item.created",
                occurred_at=now,
                actor_id=None,
                organization_id="org-1",
                workspace_id=None,
                project_id=None,
                entity_type="work_item",
                entity_id="work-1",
                correlation_id="",
                payload={"title": "Task"},
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "correlation_id" in str(e)


def test_create_outbox_event_payload_persistence() -> None:
    """Test that complex payloads are properly persisted."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        session.add(organization)
        session.commit()

        now = datetime.now(timezone.utc)
        complex_payload: dict[str, object] = {
            "type": "task",
            "title": "New Task",
            "description": "A detailed description",
            "priority": "high",
            "tags": ["urgent", "bug"],
            "metadata": {"version": 1, "draft": False},
        }

        event = create_outbox_event(
            session=session,
            event_type="work_item.created",
            occurred_at=now,
            actor_id=None,
            organization_id="org-1",
            workspace_id=None,
            project_id=None,
            entity_type="work_item",
            entity_id="work-1",
            correlation_id="corr-1",
            payload=complex_payload,
        )
        session.commit()

        result = session.scalars(select(EventOutbox).filter_by(id=event.id)).first()
        assert result is not None
        assert result.payload["type"] == "task"
        tags = result.payload.get("tags")
        assert tags == ["urgent", "bug"]
        metadata = result.payload.get("metadata")
        assert isinstance(metadata, dict)
        assert metadata.get("version") == 1
