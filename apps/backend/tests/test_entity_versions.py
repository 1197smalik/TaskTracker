"""Tests for entity versioning model."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.audit.models import AuditLog, EntityVersion
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


def test_entity_version_creation() -> None:
    """Test basic entity version creation."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        audit_log = AuditLog(
            id="audit-1",
            actor_type="system",
            organization_id="org-1",
            entity_type="work_item",
            entity_id="work-1",
            action="work_item.created",
            correlation_id="corr-1",
        )
        entity_version = EntityVersion(
            audit_log_id="audit-1",
            entity_type="work_item",
            entity_id="work-1",
            version_number=1,
            entity_snapshot={
                "type": "task",
                "status": "todo",
                "title": "New Task",
            },
            organization_id="org-1",
        )

        session.add_all([organization, audit_log, entity_version])
        session.commit()

        result = session.scalars(select(EntityVersion).filter_by(id=entity_version.id)).first()
        assert result is not None
        assert result.entity_type == "work_item"
        assert result.entity_id == "work-1"
        assert result.version_number == 1
        assert result.entity_snapshot == {
            "type": "task",
            "status": "todo",
            "title": "New Task",
        }


def test_entity_version_audit_log_reference() -> None:
    """Test that entity version maintains reference to audit log."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        audit_log = AuditLog(
            id="audit-2",
            actor_type="user",
            actor_id="user-1",
            organization_id="org-1",
            entity_type="work_item",
            entity_id="work-1",
            action="work_item.transitioned",
            correlation_id="corr-2",
        )
        entity_version = EntityVersion(
            audit_log_id="audit-2",
            entity_type="work_item",
            entity_id="work-1",
            version_number=2,
            entity_snapshot={
                "status": "review",
            },
            organization_id="org-1",
        )

        session.add_all([organization, audit_log, entity_version])
        session.commit()

        result = session.scalars(select(EntityVersion).filter_by(id=entity_version.id)).first()
        assert result is not None
        assert result.audit_log_id == "audit-2"

        retrieved_audit = session.get(AuditLog, result.audit_log_id)
        assert retrieved_audit is not None
        assert retrieved_audit.action == "work_item.transitioned"


def test_entity_version_sequential_versioning() -> None:
    """Test multiple versions of same entity."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        session.add(organization)
        session.commit()

        entity_id = "work-1"
        org_id = "org-1"

        # Create version 1
        audit_log_1 = AuditLog(
            id="audit-3",
            actor_type="system",
            organization_id=org_id,
            entity_type="work_item",
            entity_id=entity_id,
            action="work_item.created",
            correlation_id="corr-1",
        )
        version_1 = EntityVersion(
            audit_log_id="audit-3",
            entity_type="work_item",
            entity_id=entity_id,
            version_number=1,
            entity_snapshot={"status": "todo", "title": "Task"},
            organization_id=org_id,
        )
        session.add_all([audit_log_1, version_1])
        session.commit()

        # Create version 2
        audit_log_2 = AuditLog(
            id="audit-4",
            actor_type="user",
            actor_id="user-1",
            organization_id=org_id,
            entity_type="work_item",
            entity_id=entity_id,
            action="work_item.updated",
            correlation_id="corr-2",
        )
        version_2 = EntityVersion(
            audit_log_id="audit-4",
            entity_type="work_item",
            entity_id=entity_id,
            version_number=2,
            entity_snapshot={"status": "review", "title": "Task Review"},
            organization_id=org_id,
        )
        session.add_all([audit_log_2, version_2])
        session.commit()

        versions = list(
            session.scalars(
                select(EntityVersion)
                .filter_by(entity_type="work_item", entity_id=entity_id)
                .order_by(EntityVersion.version_number)
            )
        )
        assert len(versions) == 2
        assert versions[0].version_number == 1
        assert versions[0].entity_snapshot["status"] == "todo"
        assert versions[1].version_number == 2
        assert versions[1].entity_snapshot["status"] == "review"


def test_entity_version_organization_scoping() -> None:
    """Test that entity versions are scoped to organization."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        org1 = Organization(id="org-1", name="Acme")
        org2 = Organization(id="org-2", name="OtherCo")
        session.add_all([org1, org2])
        session.commit()

        # Version in org-1
        audit_log_1 = AuditLog(
            id="audit-5",
            actor_type="system",
            organization_id="org-1",
            entity_type="work_item",
            entity_id="work-1",
            action="work_item.created",
            correlation_id="corr-1",
        )
        version_1 = EntityVersion(
            audit_log_id="audit-5",
            entity_type="work_item",
            entity_id="work-1",
            version_number=1,
            entity_snapshot={"title": "Task in Org1"},
            organization_id="org-1",
        )

        # Version in org-2
        audit_log_2 = AuditLog(
            id="audit-6",
            actor_type="system",
            organization_id="org-2",
            entity_type="work_item",
            entity_id="work-1",
            action="work_item.created",
            correlation_id="corr-2",
        )
        version_2 = EntityVersion(
            audit_log_id="audit-6",
            entity_type="work_item",
            entity_id="work-1",
            version_number=1,
            entity_snapshot={"title": "Task in Org2"},
            organization_id="org-2",
        )

        session.add_all([audit_log_1, version_1, audit_log_2, version_2])
        session.commit()

        org1_versions = list(
            session.scalars(select(EntityVersion).filter_by(organization_id="org-1"))
        )
        org2_versions = list(
            session.scalars(select(EntityVersion).filter_by(organization_id="org-2"))
        )

        assert len(org1_versions) == 1
        assert len(org2_versions) == 1
        assert org1_versions[0].entity_snapshot["title"] == "Task in Org1"
        assert org2_versions[0].entity_snapshot["title"] == "Task in Org2"


def test_entity_version_timestamp() -> None:
    """Test that entity version captures created_at timestamp."""
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        audit_log = AuditLog(
            id="audit-7",
            actor_type="system",
            organization_id="org-1",
            entity_type="work_item",
            entity_id="work-1",
            action="work_item.created",
            correlation_id="corr-1",
        )
        before_time = datetime.now(timezone.utc)
        entity_version = EntityVersion(
            audit_log_id="audit-7",
            entity_type="work_item",
            entity_id="work-1",
            version_number=1,
            entity_snapshot={"title": "Task"},
            organization_id="org-1",
        )
        session.add_all([organization, audit_log, entity_version])
        session.commit()

        result = session.scalars(select(EntityVersion).filter_by(id=entity_version.id)).first()
        assert result is not None
        assert result.created_at is not None
        assert result.created_at >= before_time
        assert result.created_at.tzinfo is not None
