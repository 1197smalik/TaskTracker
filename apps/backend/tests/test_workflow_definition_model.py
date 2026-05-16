"""Tests for the WorkflowDefinition SQLAlchemy model."""

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)

from taskmaster_backend.db.base import Base
from taskmaster_backend.workflows.models import WorkflowDefinition


def test_workflow_definition_model_is_registered_with_base_metadata() -> None:
    assert WorkflowDefinition.__table__ is Base.metadata.tables["workflow_definitions"]


def test_workflow_definition_model_has_expected_columns() -> None:
    columns = WorkflowDefinition.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "project_id",
        "name",
        "description",
        "version",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["project_id"].type, String)
    assert isinstance(columns["name"].type, String)
    assert isinstance(columns["description"].type, Text)
    assert isinstance(columns["version"].type, Integer)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_workflow_definition_model_has_project_scoped_constraints_and_indexes() -> None:
    table = WorkflowDefinition.__table__
    assert isinstance(table, Table)

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    ]
    foreign_key_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
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
        constraint.name == "uq_workflow_definitions_project_id_name_version"
        and tuple(column.name for column in constraint.columns)
        == ("project_id", "name", "version")
        for constraint in unique_constraints
    )
    assert any(
        tuple(column.name for column in constraint.columns) == ("project_id",)
        and tuple(element.target_fullname for element in constraint.elements)
        == ("projects.id",)
        for constraint in foreign_key_constraints
    )
    assert any(
        constraint.name == "ck_workflow_definitions_version_positive"
        for constraint in check_constraints
    )
    assert index_columns["ix_workflow_definitions_project_id"] == ("project_id",)
    assert index_columns["ix_workflow_definitions_project_id_name"] == ("project_id", "name")


def test_workflow_definition_model_does_not_create_later_story_fields() -> None:
    columns = WorkflowDefinition.__table__.columns

    assert "state_id" not in columns
    assert "transition_id" not in columns
    assert "rule_config" not in columns
    assert "automation_metadata" not in columns
    assert "visual_builder_state" not in columns
    assert "event_outbox_id" not in columns
