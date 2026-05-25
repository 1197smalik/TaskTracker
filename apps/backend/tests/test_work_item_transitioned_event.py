"""Tests for work_item.transitioned event emission."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.audit.models import EventOutbox
from taskmaster_backend.audit.service import create_outbox_event
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization, Workspace
from taskmaster_backend.projects.models import Project
from taskmaster_backend.work_items.repository import create_work_item
from taskmaster_backend.work_items.schemas import WorkItemCreateRequest


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def test_work_item_transitioned_event_basic() -> None:
    """Test that work_item.transitioned event has required fields."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        # Setup organizations and workspace
        org = Organization(id="org-1", name="Acme")
        workspace = Workspace(id="ws-1", organization_id="org-1", name="Platform")
        project = Project(
            id="proj-1",
            workspace_id="ws-1",
            key="TM",
            name="TaskMaster",
        )

        session.add_all([org, workspace, project])
        session.commit()

        # Create work item
        request = WorkItemCreateRequest(
            type="task",
            status="todo",
            title="Task",
        )
        work_item = create_work_item(session, project.id, request, commit=False)

        # Create transition event
        correlation_id = str(uuid4())
        now = datetime.now(timezone.utc)

        event = create_outbox_event(
            session,
            event_type="work_item.transitioned",
            occurred_at=now,
            actor_id=None,
            organization_id=org.id,
            workspace_id=workspace.id,
            project_id=project.id,
            entity_type="work_item",
            entity_id=work_item.id,
            correlation_id=correlation_id,
            payload={
                "source_state_id": "state-1",
                "target_state_id": "state-2",
                "transition_id": "trans-1",
            },
        )

        session.commit()

        # Verify event fields
        result = session.scalars(select(EventOutbox).filter_by(id=event.id)).first()
        assert result is not None
        assert result.event_type == "work_item.transitioned"
        assert result.entity_type == "work_item"
        assert result.entity_id == work_item.id
        assert result.organization_id == org.id
        assert result.workspace_id == workspace.id
        assert result.project_id == project.id
        assert result.status == "pending"


def test_work_item_transitioned_event_payload() -> None:
    """Test that work_item.transitioned event payload contains state transition data."""
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

        session.add_all([org, workspace, project])
        session.commit()

        # Create work item
        request = WorkItemCreateRequest(
            type="bug",
            status="new",
            title="Critical Bug",
        )
        work_item = create_work_item(session, project.id, request, commit=False)

        # Create event with detailed payload
        now = datetime.now(timezone.utc)
        event = create_outbox_event(
            session,
            event_type="work_item.transitioned",
            occurred_at=now,
            actor_id=None,
            organization_id=org.id,
            workspace_id=workspace.id,
            project_id=project.id,
            entity_type="work_item",
            entity_id=work_item.id,
            correlation_id=str(uuid4()),
            payload={
                "source_state_id": "state-1",
                "target_state_id": "state-2",
                "transition_id": "trans-xyz",
            },
        )

        session.commit()

        # Verify payload contains all transition information
        result = session.scalars(select(EventOutbox).filter_by(id=event.id)).first()
        assert result is not None
        assert result.payload["source_state_id"] == "state-1"
        assert result.payload["target_state_id"] == "state-2"
        assert result.payload["transition_id"] == "trans-xyz"


def test_multiple_work_item_transitioned_events() -> None:
    """Test that multiple transitions generate separate events."""
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

        session.add_all([org, workspace, project])
        session.commit()

        now = datetime.now(timezone.utc)

        # Create first transition event
        request1 = WorkItemCreateRequest(
            type="task",
            status="todo",
            title="Task 1",
            current_state_id="state-1",
        )
        work_item1 = create_work_item(session, project.id, request1, commit=False)

        create_outbox_event(
            session,
            event_type="work_item.transitioned",
            occurred_at=now,
            actor_id=None,
            organization_id=org.id,
            workspace_id=workspace.id,
            project_id=project.id,
            entity_type="work_item",
            entity_id=work_item1.id,
            correlation_id=str(uuid4()),
            payload={
                "source_state_id": "state-1",
                "target_state_id": "state-2",
            },
        )

        # Create second transition event (same work item, different transition)
        create_outbox_event(
            session,
            event_type="work_item.transitioned",
            occurred_at=now,
            actor_id=None,
            organization_id=org.id,
            workspace_id=workspace.id,
            project_id=project.id,
            entity_type="work_item",
            entity_id=work_item1.id,
            correlation_id=str(uuid4()),
            payload={
                "source_state_id": "state-2",
                "target_state_id": "state-3",
            },
        )

        session.commit()

        # Verify both events exist
        events = list(
            session.scalars(
                select(EventOutbox).filter_by(event_type="work_item.transitioned")
            )
        )
        assert len(events) == 2
        assert all(e.entity_id == work_item1.id for e in events)


def test_work_item_transitioned_event_correlation_tracking() -> None:
    """Test that correlation ID is preserved for request tracing."""
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

        session.add_all([org, workspace, project])
        session.commit()

        request = WorkItemCreateRequest(
            type="task",
            status="todo",
            title="Task",
        )
        work_item = create_work_item(session, project.id, request, commit=False)

        # Use specific correlation ID for tracing
        correlation_id = "corr-transition-123-xyz"
        now = datetime.now(timezone.utc)

        event = create_outbox_event(
            session,
            event_type="work_item.transitioned",
            occurred_at=now,
            actor_id=None,
            organization_id=org.id,
            workspace_id=workspace.id,
            project_id=project.id,
            entity_type="work_item",
            entity_id=work_item.id,
            correlation_id=correlation_id,
            payload={
                "source_state_id": "state-1",
                "target_state_id": "state-2",
            },
        )

        session.commit()

        # Verify correlation ID for audit trail linking
        result = session.scalars(select(EventOutbox).filter_by(id=event.id)).first()
        assert result is not None
        assert result.correlation_id == correlation_id


def test_work_item_transitioned_event_timestamp() -> None:
    """Test that transition event has accurate timestamp."""
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

        session.add_all([org, workspace, project])
        session.commit()

        request = WorkItemCreateRequest(
            type="task",
            status="todo",
            title="Task",
        )
        work_item = create_work_item(session, project.id, request, commit=False)

        occurred_at = datetime.now(timezone.utc)
        event = create_outbox_event(
            session,
            event_type="work_item.transitioned",
            occurred_at=occurred_at,
            actor_id=None,
            organization_id=org.id,
            workspace_id=workspace.id,
            project_id=project.id,
            entity_type="work_item",
            entity_id=work_item.id,
            correlation_id=str(uuid4()),
            payload={
                "source_state_id": "state-1",
                "target_state_id": "state-2",
            },
        )

        session.commit()

        result = session.scalars(select(EventOutbox).filter_by(id=event.id)).first()
        assert result is not None
        assert result.occurred_at == occurred_at
        assert result.created_at is not None
        assert result.created_at.tzinfo is not None
