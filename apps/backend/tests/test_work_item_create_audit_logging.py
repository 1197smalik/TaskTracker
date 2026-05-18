"""Tests for audit logging during WorkItem creation."""

from __future__ import annotations

import pytest
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.audit.models import AuditLog
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization, Workspace
from taskmaster_backend.projects.models import Project
from taskmaster_backend.work_items.models import WorkItem
from taskmaster_backend.work_items.routes import create_project_work_item
from taskmaster_backend.work_items.schemas import WorkItemCreateRequest, WorkItemResponse


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def _seed_project(session_factory: sessionmaker[Session]) -> dict[str, str]:
    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        workspace = Workspace(id="workspace-1", organization_id="org-1", name="Platform")
        project = Project(id="project-1", workspace_id="workspace-1", key="TM", name="TaskMaster")
        session.add_all([organization, workspace, project])
        session.commit()
        return {
            "organization_id": organization.id,
            "workspace_id": workspace.id,
            "project_id": project.id,
        }


def test_work_item_create_writes_audit_log_with_stable_action_and_entity() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_project(session_factory)
    request = WorkItemCreateRequest(
        type="task",
        status="todo",
        title="Write audited create endpoint",
        description="Persist and audit the new work item.",
    )

    with session_factory() as session:
        response = create_project_work_item(ids["project_id"], request, session)

    assert isinstance(response, WorkItemResponse)
    assert response.project_id == ids["project_id"]
    assert response.title == "Write audited create endpoint"

    with session_factory() as session:
        work_item = session.scalars(select(WorkItem)).one()
        audit_log = session.scalars(select(AuditLog)).one()

    assert work_item.id == response.id
    assert audit_log.entity_type == "work_item"
    assert audit_log.entity_id == response.id
    assert audit_log.action == "work_item.created"
    assert audit_log.organization_id == ids["organization_id"]
    assert audit_log.workspace_id == ids["workspace_id"]
    assert audit_log.project_id == ids["project_id"]
    assert audit_log.actor_id is None
    assert audit_log.actor_type == "system"
    assert audit_log.before_summary is None
    assert audit_log.after_summary == {
        "type": "task",
        "status": "todo",
        "title": "Write audited create endpoint",
    }
    assert audit_log.correlation_id != ""


def test_work_item_create_unknown_project_does_not_write_audit_log() -> None:
    session_factory = _create_test_session_factory()
    request = WorkItemCreateRequest(
        type="task",
        status="todo",
        title="Unknown project",
    )

    with session_factory() as session:
        response = create_project_work_item("missing-project", request, session)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404

    with session_factory() as session:
        assert list(session.scalars(select(WorkItem)).all()) == []
        assert list(session.scalars(select(AuditLog)).all()) == []


def test_work_item_create_rolls_back_when_audit_write_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_project(session_factory)
    request = WorkItemCreateRequest(
        type="task",
        status="todo",
        title="Rollback on audit failure",
    )

    def _raise_audit_failure(*args: object, **kwargs: object) -> None:
        raise RuntimeError("audit write failed")

    monkeypatch.setattr(
        "taskmaster_backend.work_items.routes.write_audit_log",
        _raise_audit_failure
    )

    with pytest.raises(RuntimeError, match="audit write failed"):
        with session_factory() as session:
            create_project_work_item(ids["project_id"], request, session)

    with session_factory() as session:
        assert list(session.scalars(select(WorkItem)).all()) == []
        assert list(session.scalars(select(AuditLog)).all()) == []
