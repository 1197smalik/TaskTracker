"""Tests for event outbox model."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.audit.models import EventOutbox
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization, Workspace
from taskmaster_backend.projects.models import Project


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def test_event_outbox_creation() -> None:
    """Test basic event outbox creation."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        event = EventOutbox(
            event_id="event-1",
            event_type="work_item.created",
            occurred_at=datetime.now(timezone.utc),
            organization_id="org-1",
            entity_type="work_item",
            entity_id="work-1",
            correlation_id="corr-1",
            payload={
                "type": "task",
                "title": "New Task",
                "status": "todo",
            },
        )

        session.add_all([organization, event])
        session.commit()

        result = session.scalars(select(EventOutbox).filter_by(id=event.id)).first()
        assert result is not None
        assert result.event_id == "event-1"
        assert result.event_type == "work_item.created"
        assert result.status == "pending"
        assert result.retry_count == 0
        assert result.payload["title"] == "New Task"


def test_event_outbox_status_workflow() -> None:
    """Test event outbox status transitions."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        now = datetime.now(timezone.utc)
        event = EventOutbox(
            event_id="event-2",
            event_type="work_item.transitioned",
            occurred_at=now,
            organization_id="org-1",
            entity_type="work_item",
            entity_id="work-1",
            correlation_id="corr-2",
            payload={"old_state": "todo", "new_state": "review"},
        )

        session.add_all([organization, event])
        session.commit()

        # Simulate dispatch
        event.status = "dispatched"
        event.dispatched_at = now + timedelta(seconds=1)
        session.commit()

        result = session.scalars(select(EventOutbox).filter_by(id=event.id)).first()
        assert result is not None
        assert result.status == "dispatched"
        assert result.dispatched_at is not None

        # Simulate retry on failure
        event.status = "pending"
        event.retry_count = 1
        session.commit()

        result = session.scalars(select(EventOutbox).filter_by(id=event.id)).first()
        assert result is not None
        assert result.status == "pending"
        assert result.retry_count == 1


def test_event_outbox_scoping() -> None:
    """Test event outbox organization/workspace/project scoping."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        org = Organization(id="org-1", name="Acme")
        workspace = Workspace(id="ws-1", organization_id="org-1", name="Platform")
        project = Project(
            id="proj-1",
            workspace_id="ws-1",
            key="TM",
            name="TaskMaster",
        )

        event = EventOutbox(
            event_id="event-3",
            event_type="work_item.created",
            occurred_at=datetime.now(timezone.utc),
            organization_id="org-1",
            workspace_id="ws-1",
            project_id="proj-1",
            entity_type="work_item",
            entity_id="work-1",
            correlation_id="corr-3",
            payload={"type": "task"},
        )

        session.add_all([org, workspace, project, event])
        session.commit()

        result = session.scalars(select(EventOutbox).filter_by(id=event.id)).first()
        assert result is not None
        assert result.organization_id == "org-1"
        assert result.workspace_id == "ws-1"
        assert result.project_id == "proj-1"


def test_event_outbox_pending_query() -> None:
    """Test querying pending events."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        session.add(organization)
        session.commit()

        now = datetime.now(timezone.utc)

        # Create three events: 2 pending, 1 dispatched
        event1 = EventOutbox(
            event_id="event-1",
            event_type="work_item.created",
            occurred_at=now,
            organization_id="org-1",
            entity_type="work_item",
            entity_id="work-1",
            correlation_id="corr-1",
            payload={"title": "Task 1"},
        )
        event2 = EventOutbox(
            event_id="event-2",
            event_type="work_item.created",
            occurred_at=now,
            organization_id="org-1",
            entity_type="work_item",
            entity_id="work-2",
            correlation_id="corr-2",
            payload={"title": "Task 2"},
        )
        event3 = EventOutbox(
            event_id="event-3",
            event_type="work_item.created",
            occurred_at=now,
            organization_id="org-1",
            entity_type="work_item",
            entity_id="work-3",
            correlation_id="corr-3",
            payload={"title": "Task 3"},
            status="dispatched",
            dispatched_at=now,
        )

        session.add_all([event1, event2, event3])
        session.commit()

        pending = list(session.scalars(select(EventOutbox).filter_by(status="pending")))
        assert len(pending) == 2
        assert all(e.status == "pending" for e in pending)

        dispatched = list(session.scalars(select(EventOutbox).filter_by(status="dispatched")))
        assert len(dispatched) == 1
        assert dispatched[0].status == "dispatched"


def test_event_outbox_unique_event_id() -> None:
    """Test that event_id must be unique."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        session.add(organization)
        session.commit()

        now = datetime.now(timezone.utc)

        event1 = EventOutbox(
            event_id="event-1",
            event_type="work_item.created",
            occurred_at=now,
            organization_id="org-1",
            entity_type="work_item",
            entity_id="work-1",
            correlation_id="corr-1",
            payload={"title": "Task 1"},
        )

        session.add(event1)
        session.commit()

        # Try to create another event with same event_id
        event2 = EventOutbox(
            event_id="event-1",
            event_type="work_item.created",
            occurred_at=now,
            organization_id="org-1",
            entity_type="work_item",
            entity_id="work-2",
            correlation_id="corr-2",
            payload={"title": "Task 2"},
        )

        session.add(event2)
        try:
            session.commit()
            assert False, "Should have raised IntegrityError"
        except Exception:
            session.rollback()


def test_event_outbox_timestamp() -> None:
    """Test event outbox timestamps."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        now = datetime.now(timezone.utc)

        event = EventOutbox(
            event_id="event-1",
            event_type="work_item.created",
            occurred_at=now,
            organization_id="org-1",
            entity_type="work_item",
            entity_id="work-1",
            correlation_id="corr-1",
            payload={"title": "Task"},
        )

        session.add_all([organization, event])
        session.commit()

        result = session.scalars(select(EventOutbox).filter_by(id=event.id)).first()
        assert result is not None
        assert result.occurred_at == now
        assert result.created_at is not None
        assert result.updated_at is not None
        assert result.created_at.tzinfo is not None
        assert result.updated_at.tzinfo is not None


def test_event_outbox_retry_tracking() -> None:
    """Test tracking retries for failed events."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        session.add(organization)
        session.commit()

        event = EventOutbox(
            event_id="event-1",
            event_type="work_item.created",
            occurred_at=datetime.now(timezone.utc),
            organization_id="org-1",
            entity_type="work_item",
            entity_id="work-1",
            correlation_id="corr-1",
            payload={"title": "Task"},
        )

        session.add(event)
        session.commit()

        # Simulate retries
        event.retry_count = 1
        session.commit()

        event.retry_count = 2
        session.commit()

        event.retry_count = 3
        event.status = "dead_letter"
        session.commit()

        result = session.scalars(select(EventOutbox).filter_by(id=event.id)).first()
        assert result is not None
        assert result.retry_count == 3
        assert result.status == "dead_letter"
