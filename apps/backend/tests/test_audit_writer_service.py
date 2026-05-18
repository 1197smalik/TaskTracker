"""Tests for the audit writer service."""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.audit.models import AuditLog
from taskmaster_backend.audit.service import AuditLogWriteRequest, write_audit_log
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


def _seed_scope_records(session_factory: sessionmaker[Session]) -> dict[str, str]:
    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        workspace = Workspace(id="workspace-1", organization_id="org-1", name="Platform")
        project = Project(
            id="project-1",
            workspace_id="workspace-1",
            key="TM",
            name="TaskMaster",
        )
        actor = User(
            id="user-1",
            email="user@example.com",
            password_hash="hashed",
        )
        session.add_all([organization, workspace, project, actor])
        session.commit()
        return {
            "organization_id": organization.id,
            "workspace_id": workspace.id,
            "project_id": project.id,
            "actor_id": actor.id,
        }


def test_audit_writer_persists_audit_log_row() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_scope_records(session_factory)

    with session_factory() as session:
        audit_log = write_audit_log(
            session,
            AuditLogWriteRequest(
                actor_id=ids["actor_id"],
                actor_type="user",
                organization_id=ids["organization_id"],
                workspace_id=ids["workspace_id"],
                project_id=ids["project_id"],
                entity_type="work_item",
                entity_id="work-item-1",
                action="work_item.created",
                before_summary={"status": None},
                after_summary={"status": "todo"},
                diff_reference="entity-version-1",
                ip_address="127.0.0.1",
                user_agent="pytest",
                correlation_id="corr-1",
            ),
        )

    assert audit_log.id != ""
    assert audit_log.actor_id == ids["actor_id"]
    assert audit_log.entity_type == "work_item"
    assert audit_log.action == "work_item.created"
    assert audit_log.correlation_id == "corr-1"

    with session_factory() as session:
        persisted = session.scalars(select(AuditLog)).one()
        assert persisted.actor_id == ids["actor_id"]
        assert persisted.before_summary == {"status": None}
        assert persisted.after_summary == {"status": "todo"}
        assert persisted.diff_reference == "entity-version-1"


def test_audit_writer_requires_non_empty_required_fields() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_scope_records(session_factory)

    with session_factory() as session:
        with pytest.raises(ValueError, match="actor_type is required"):
            write_audit_log(
                session,
                AuditLogWriteRequest(
                    actor_type="",
                    organization_id=ids["organization_id"],
                    entity_type="work_item",
                    entity_id="work-item-1",
                    action="work_item.created",
                    correlation_id="corr-1",
                ),
            )

        with pytest.raises(ValueError, match="correlation_id is required"):
            write_audit_log(
                session,
                AuditLogWriteRequest(
                    actor_type="user",
                    organization_id=ids["organization_id"],
                    entity_type="work_item",
                    entity_id="work-item-1",
                    action="work_item.created",
                    correlation_id=" ",
                ),
            )


def test_audit_writer_propagates_scope_fields() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_scope_records(session_factory)

    with session_factory() as session:
        audit_log = write_audit_log(
            session,
            AuditLogWriteRequest(
                actor_type="user",
                organization_id=ids["organization_id"],
                workspace_id=ids["workspace_id"],
                project_id=ids["project_id"],
                entity_type="workflow_definition",
                entity_id="workflow-1",
                action="workflow.updated",
                correlation_id="corr-2",
            ),
        )

    assert audit_log.organization_id == ids["organization_id"]
    assert audit_log.workspace_id == ids["workspace_id"]
    assert audit_log.project_id == ids["project_id"]


def test_audit_writer_persists_actor_entity_action_and_correlation() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_scope_records(session_factory)

    with session_factory() as session:
        audit_log = write_audit_log(
            session,
            AuditLogWriteRequest(
                actor_id=ids["actor_id"],
                actor_type="api_token",
                organization_id=ids["organization_id"],
                entity_type="permission",
                entity_id="permission-1",
                action="permission.denied",
                correlation_id="corr-3",
            ),
        )

    assert audit_log.actor_id == ids["actor_id"]
    assert audit_log.actor_type == "api_token"
    assert audit_log.entity_type == "permission"
    assert audit_log.entity_id == "permission-1"
    assert audit_log.action == "permission.denied"
    assert audit_log.correlation_id == "corr-3"


def test_audit_writer_is_append_only() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_scope_records(session_factory)

    with session_factory() as session:
        first = write_audit_log(
            session,
            AuditLogWriteRequest(
                actor_type="user",
                organization_id=ids["organization_id"],
                entity_type="work_item",
                entity_id="work-item-1",
                action="work_item.created",
                correlation_id="corr-4",
            ),
        )
        second = write_audit_log(
            session,
            AuditLogWriteRequest(
                actor_type="user",
                organization_id=ids["organization_id"],
                entity_type="work_item",
                entity_id="work-item-1",
                action="work_item.updated",
                correlation_id="corr-5",
            ),
        )

    assert first.id != second.id

    with session_factory() as session:
        persisted = list(
            session.scalars(
                select(AuditLog).order_by(AuditLog.created_at.asc())
            ).all()
        )
        assert len(persisted) == 2
        assert [item.action for item in persisted] == ["work_item.created", "work_item.updated"]


def test_audit_writer_handles_nullable_fields() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_scope_records(session_factory)

    with session_factory() as session:
        audit_log = write_audit_log(
            session,
            AuditLogWriteRequest(
                actor_type="system",
                organization_id=ids["organization_id"],
                entity_type="workflow_definition",
                entity_id="workflow-1",
                action="workflow.updated",
                correlation_id="corr-6",
                before_summary=None,
                after_summary=None,
                diff_reference=None,
                ip_address=None,
                user_agent=None,
            ),
        )

    assert audit_log.actor_id is None
    assert audit_log.workspace_id is None
    assert audit_log.project_id is None
    assert audit_log.before_summary is None
    assert audit_log.after_summary is None
    assert audit_log.diff_reference is None
    assert audit_log.ip_address is None
    assert audit_log.user_agent is None
