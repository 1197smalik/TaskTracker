"""Tests for the WorkflowTransition SQLAlchemy model."""

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    String,
    Table,
    UniqueConstraint,
)

from taskmaster_backend.db.base import Base
from taskmaster_backend.workflows.models import WorkflowTransition


def test_workflow_transition_model_is_registered_with_base_metadata() -> None:
    assert WorkflowTransition.__table__ is Base.metadata.tables["workflow_transitions"]


def test_workflow_transition_model_has_expected_columns() -> None:
    columns = WorkflowTransition.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "workflow_definition_id",
        "source_state_id",
        "target_state_id",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["workflow_definition_id"].type, String)
    assert isinstance(columns["source_state_id"].type, String)
    assert isinstance(columns["target_state_id"].type, String)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_workflow_transition_model_has_definition_scoped_constraints() -> None:
    table = WorkflowTransition.__table__
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

    assert any(
        constraint.name
        == "uq_workflow_transitions_workflow_definition_id_source_target"
        and tuple(column.name for column in constraint.columns)
        == ("workflow_definition_id", "source_state_id", "target_state_id")
        for constraint in unique_constraints
    )
    assert any(
        constraint.name == "ck_workflow_transitions_distinct_states"
        for constraint in check_constraints
    )


def test_workflow_transition_model_references_definition_and_states() -> None:
    table = WorkflowTransition.__table__
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

    assert foreign_keys[("workflow_definition_id",)] == ("workflow_definitions.id",)
    assert foreign_keys[("source_state_id",)] == ("workflow_states.id",)
    assert foreign_keys[("target_state_id",)] == ("workflow_states.id",)


def test_workflow_transition_model_has_lookup_indexes() -> None:
    table = WorkflowTransition.__table__
    assert isinstance(table, Table)

    index_columns: dict[str, tuple[str, ...]] = {
        str(index.name): tuple(column.name for column in index.columns)
        for index in table.indexes
        if isinstance(index, Index)
    }

    assert index_columns["ix_workflow_transitions_workflow_definition_id"] == (
        "workflow_definition_id",
    )
    assert index_columns[
        "ix_workflow_transitions_workflow_definition_id_source_state_id"
    ] == (
        "workflow_definition_id",
        "source_state_id",
    )
    assert index_columns[
        "ix_workflow_transitions_workflow_definition_id_target_state_id"
    ] == (
        "workflow_definition_id",
        "target_state_id",
    )


def test_workflow_transition_model_does_not_create_later_story_fields() -> None:
    columns = WorkflowTransition.__table__.columns

    assert "rule_config" not in columns
    assert "guard_rule_id" not in columns
    assert "required_field_rule_id" not in columns
    assert "role_rule_id" not in columns
    assert "automation_metadata" not in columns
    assert "event_outbox_id" not in columns
    assert "script" not in columns
