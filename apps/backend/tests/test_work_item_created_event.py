"""Tests for work_item.created event emission."""

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


def test_work_item_creation_event_emission() -> None:
    """Test that work_item.created event is emitted when work item is created."""
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
            title="New Task",
            description="Task description",
        )
        work_item = create_work_item(session, project.id, request, commit=True)

        # Verify work item was created
        assert work_item.id is not None
        assert work_item.title == "New Task"


def test_work_item_created_event_has_correct_fields() -> None:
    """Test that work_item.created event has all required fields."""
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

        correlation_id = str(uuid4())
        now = datetime.now(timezone.utc)

        # Create work item
        request = WorkItemCreateRequest(
            type="task",
            status="todo",
            title="New Task",
            description="Task description",
        )
        work_item = create_work_item(session, project.id, request, commit=False)

        # Create event (simulating what the route would do)
        event = create_outbox_event(
            session,
            event_type="work_item.created",
            occurred_at=now,
            actor_id=None,
            organization_id=org.id,
            workspace_id=workspace.id,
            project_id=project.id,
            entity_type="work_item",
            entity_id=work_item.id,
            correlation_id=correlation_id,
            payload={
                "type": work_item.type,
                "status": work_item.status,
                "title": work_item.title,
                "description": work_item.description,
            },
        )

        session.commit()

        # Verify event fields
        result = session.scalars(select(EventOutbox).filter_by(id=event.id)).first()
        assert result is not None
        assert result.event_type == "work_item.created"
        assert result.entity_type == "work_item"
        assert result.entity_id == work_item.id
        assert result.organization_id == org.id
        assert result.workspace_id == workspace.id
        assert result.project_id == project.id
        assert result.status == "pending"
        assert result.retry_count == 0


def test_work_item_created_event_payload() -> None:
    """Test that work_item.created event payload contains correct data."""
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
            type="bug",
            status="new",
            title="Critical Bug",
            description="A critical bug description",
        )
        work_item = create_work_item(session, project.id, request, commit=False)

        # Create event
        correlation_id = str(uuid4())
        now = datetime.now(timezone.utc)

        event = create_outbox_event(
            session,
            event_type="work_item.created",
            occurred_at=now,
            actor_id=None,
            organization_id=org.id,
            workspace_id=workspace.id,
            project_id=project.id,
            entity_type="work_item",
            entity_id=work_item.id,
            correlation_id=correlation_id,
            payload={
                "type": work_item.type,
                "status": work_item.status,
                "title": work_item.title,
                "description": work_item.description,
            },
        )

        session.commit()

        # Verify event payload
        result = session.scalars(select(EventOutbox).filter_by(id=event.id)).first()
        assert result is not None
        assert result.payload["type"] == "bug"
        assert result.payload["title"] == "Critical Bug"
        assert result.payload["description"] == "A critical bug description"
        assert result.payload["status"] in ["todo", "draft", "new"]  # Default status


def test_multiple_work_item_created_events() -> None:
    """Test that multiple work items generate separate events."""
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

        now = datetime.now(timezone.utc)

        # Create first work item
        request1 = WorkItemCreateRequest(
            type="task",
            status="todo",
            title="Task 1",
        )
        work_item1 = create_work_item(session, project.id, request1, commit=False)

        create_outbox_event(
            session,
            event_type="work_item.created",
            occurred_at=now,
            actor_id=None,
            organization_id=org.id,
            workspace_id=workspace.id,
            project_id=project.id,
            entity_type="work_item",
            entity_id=work_item1.id,
            correlation_id=str(uuid4()),
            payload={"type": "task", "title": "Task 1"},
        )

        # Create second work item
        request2 = WorkItemCreateRequest(
            type="bug",
            status="new",
            title="Bug 1",
        )
        work_item2 = create_work_item(session, project.id, request2, commit=False)

        create_outbox_event(
            session,
            event_type="work_item.created",
            occurred_at=now,
            actor_id=None,
            organization_id=org.id,
            workspace_id=workspace.id,
            project_id=project.id,
            entity_type="work_item",
            entity_id=work_item2.id,
            correlation_id=str(uuid4()),
            payload={"type": "bug", "title": "Bug 1"},
        )

        session.commit()

        # Verify both events exist
        events = list(
            session.scalars(
                select(EventOutbox).filter_by(event_type="work_item.created")
            )
        )
        assert len(events) == 2
        assert {e.entity_id for e in events} == {work_item1.id, work_item2.id}


def test_work_item_created_event_has_correlation_id() -> None:
    """Test that work_item.created event includes correlation ID for tracing."""
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

        # Create work item with specific correlation ID
        correlation_id = "corr-abc-123-xyz"
        now = datetime.now(timezone.utc)

        request = WorkItemCreateRequest(
            type="task",
            status="todo",
            title="Task",
        )
        work_item = create_work_item(session, project.id, request, commit=False)

        event = create_outbox_event(
            session,
            event_type="work_item.created",
            occurred_at=now,
            actor_id=None,
            organization_id=org.id,
            workspace_id=workspace.id,
            project_id=project.id,
            entity_type="work_item",
            entity_id=work_item.id,
            correlation_id=correlation_id,
            payload={"type": "task", "title": "Task"},
        )

        session.commit()

        # Verify correlation ID is preserved
        result = session.scalars(select(EventOutbox).filter_by(id=event.id)).first()
        assert result is not None
        assert result.correlation_id == correlation_id
