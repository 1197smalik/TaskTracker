"""Tests for the AuditLog SQLAlchemy model."""

from sqlalchemy import JSON, DateTime, ForeignKeyConstraint, Index, String, Table

from taskmaster_backend.audit.models import AuditLog
from taskmaster_backend.db.base import Base


def test_audit_log_model_is_registered_with_base_metadata() -> None:
    assert AuditLog.__table__ is Base.metadata.tables["audit_logs"]


def test_audit_log_model_has_expected_columns() -> None:
    columns = AuditLog.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "actor_id",
        "actor_type",
        "organization_id",
        "workspace_id",
        "project_id",
        "entity_type",
        "entity_id",
        "action",
        "before_summary",
        "after_summary",
        "diff_reference",
        "ip_address",
        "user_agent",
        "correlation_id",
        "created_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["actor_id"].type, String)
    assert isinstance(columns["actor_type"].type, String)
    assert isinstance(columns["organization_id"].type, String)
    assert isinstance(columns["workspace_id"].type, String)
    assert isinstance(columns["project_id"].type, String)
    assert isinstance(columns["entity_type"].type, String)
    assert isinstance(columns["entity_id"].type, String)
    assert isinstance(columns["action"].type, String)
    assert isinstance(columns["before_summary"].type, JSON)
    assert isinstance(columns["after_summary"].type, JSON)
    assert isinstance(columns["diff_reference"].type, String)
    assert isinstance(columns["ip_address"].type, String)
    assert isinstance(columns["user_agent"].type, String)
    assert isinstance(columns["correlation_id"].type, String)
    assert isinstance(columns["created_at"].type, DateTime)


def test_audit_log_model_has_expected_foreign_keys_and_indexes() -> None:
    table = AuditLog.__table__
    assert isinstance(table, Table)

    foreign_key_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    foreign_keys = {
        tuple(column.name for column in constraint.columns): tuple(
            element.target_fullname for element in constraint.elements
        )
        for constraint in foreign_key_constraints
    }
    index_columns: dict[str, tuple[str, ...]] = {
        str(index.name): tuple(column.name for column in index.columns)
        for index in table.indexes
        if isinstance(index, Index)
    }

    assert foreign_keys[("actor_id",)] == ("users.id",)
    assert foreign_keys[("organization_id",)] == ("organizations.id",)
    assert foreign_keys[("workspace_id",)] == ("workspaces.id",)
    assert foreign_keys[("project_id",)] == ("projects.id",)
    assert index_columns["ix_audit_logs_actor_id"] == ("actor_id",)
    assert index_columns["ix_audit_logs_actor_id_created_at"] == ("actor_id", "created_at")
    assert index_columns["ix_audit_logs_organization_id"] == ("organization_id",)
    assert index_columns["ix_audit_logs_organization_id_created_at"] == (
        "organization_id",
        "created_at",
    )
    assert index_columns["ix_audit_logs_workspace_id"] == ("workspace_id",)
    assert index_columns["ix_audit_logs_workspace_id_created_at"] == (
        "workspace_id",
        "created_at",
    )
    assert index_columns["ix_audit_logs_project_id"] == ("project_id",)
    assert index_columns["ix_audit_logs_project_id_created_at"] == (
        "project_id",
        "created_at",
    )
    assert index_columns["ix_audit_logs_action_created_at"] == ("action", "created_at")
    assert index_columns["ix_audit_logs_entity_type_entity_id_created_at"] == (
        "entity_type",
        "entity_id",
        "created_at",
    )


def test_audit_log_model_does_not_create_later_story_fields() -> None:
    columns = AuditLog.__table__.columns

    assert "security_event_type" not in columns
    assert "entity_version_id" not in columns
    assert "event_outbox_id" not in columns
    assert "retention_policy_id" not in columns
