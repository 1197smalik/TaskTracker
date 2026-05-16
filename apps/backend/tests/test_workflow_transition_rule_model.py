"""Tests for the WorkflowTransitionRule SQLAlchemy model."""

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    String,
    Table,
    UniqueConstraint,
)

from taskmaster_backend.db.base import Base
from taskmaster_backend.workflows.models import WorkflowTransitionRule


def test_workflow_transition_rule_model_is_registered_with_base_metadata() -> None:
    assert (
        WorkflowTransitionRule.__table__
        is Base.metadata.tables["workflow_transition_rules"]
    )


def test_workflow_transition_rule_model_has_expected_columns() -> None:
    columns = WorkflowTransitionRule.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "workflow_transition_id",
        "rule_type",
        "config",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["workflow_transition_id"].type, String)
    assert isinstance(columns["rule_type"].type, String)
    assert isinstance(columns["config"].type, JSON)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_workflow_transition_rule_model_references_transition() -> None:
    table = WorkflowTransitionRule.__table__
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

    assert foreign_keys[("workflow_transition_id",)] == ("workflow_transitions.id",)


def test_workflow_transition_rule_model_has_constraints_and_indexes() -> None:
    table = WorkflowTransitionRule.__table__
    assert isinstance(table, Table)

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    ]
    check_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    ]
    index_columns: dict[str, tuple[str, ...]] = {
        str(index.name): tuple(column.name for column in index.columns)
        for index in table.indexes
        if isinstance(index, Index)
    }

    assert any(
        constraint.name == "uq_workflow_transition_rules_transition_id_rule_type"
        and tuple(column.name for column in constraint.columns)
        == ("workflow_transition_id", "rule_type")
        for constraint in unique_constraints
    )
    assert any(
        constraint.name == "ck_workflow_transition_rules_type_supported"
        for constraint in check_constraints
    )
    assert index_columns["ix_workflow_transition_rules_workflow_transition_id"] == (
        "workflow_transition_id",
    )
    assert index_columns["ix_workflow_transition_rules_transition_id_rule_type"] == (
        "workflow_transition_id",
        "rule_type",
    )


def test_workflow_transition_rule_model_does_not_create_execution_fields() -> None:
    columns = WorkflowTransitionRule.__table__.columns

    assert "script" not in columns
    assert "webhook_url" not in columns
    assert "automation_payload" not in columns
    assert "event_outbox_id" not in columns
    assert "rbac_enforcement_id" not in columns
    assert "evaluation_result" not in columns
