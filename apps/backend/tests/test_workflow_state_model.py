"""Tests for the WorkflowState SQLAlchemy model."""

from fastapi.routing import APIRoute
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Table,
    UniqueConstraint,
)

from taskmaster_backend.app import app
from taskmaster_backend.db.base import Base
from taskmaster_backend.workflows.models import WorkflowState


def test_workflow_state_model_is_registered_with_base_metadata() -> None:
    assert WorkflowState.__table__ is Base.metadata.tables["workflow_states"]


def test_workflow_state_model_has_expected_columns() -> None:
    columns = WorkflowState.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "workflow_definition_id",
        "name",
        "position",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["workflow_definition_id"].type, String)
    assert isinstance(columns["name"].type, String)
    assert isinstance(columns["position"].type, Integer)
    assert not columns["position"].nullable
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_workflow_state_model_has_definition_scoped_constraints_and_indexes() -> None:
    table = WorkflowState.__table__
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
    foreign_key_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    index_columns: dict[str, tuple[str, ...]] = {
        str(index.name): tuple(column.name for column in index.columns)
        for index in table.indexes
        if isinstance(index, Index)
    }

    assert any(
        constraint.name == "uq_workflow_states_workflow_definition_id_name"
        and tuple(column.name for column in constraint.columns)
        == ("workflow_definition_id", "name")
        for constraint in unique_constraints
    )
    assert any(
        tuple(column.name for column in constraint.columns)
        == ("workflow_definition_id",)
        and tuple(element.target_fullname for element in constraint.elements)
        == ("workflow_definitions.id",)
        for constraint in foreign_key_constraints
    )
    assert index_columns["ix_workflow_states_workflow_definition_id"] == (
        "workflow_definition_id",
    )
    assert index_columns["ix_workflow_states_workflow_definition_id_name"] == (
        "workflow_definition_id",
        "name",
    )
    assert index_columns["ix_workflow_states_workflow_definition_id_position"] == (
        "workflow_definition_id",
        "position",
    )
    assert any(
        constraint.name == "ck_workflow_states_position_non_negative"
        for constraint in check_constraints
    )


def test_workflow_state_model_does_not_create_later_story_fields() -> None:
    columns = WorkflowState.__table__.columns

    assert "from_state_id" not in columns
    assert "to_state_id" not in columns
    assert "transition_id" not in columns
    assert "rule_config" not in columns
    assert "automation_metadata" not in columns
    assert "color" not in columns
    assert "category" not in columns


def test_workflow_state_position_does_not_add_board_read_routes() -> None:
    board_mapping_routes = [
        route.path
        for route in app.routes
        if isinstance(route, APIRoute)
        and (
            "/workflow-states" in route.path
            or "/board-columns" in route.path
            or route.path.endswith("/board")
        )
    ]

    assert board_mapping_routes == []
