"""Tests for the Board SQLAlchemy model."""

from sqlalchemy import DateTime, ForeignKeyConstraint, String, Table

from taskmaster_backend.db.base import Base
from taskmaster_backend.projects.models import Board


def test_board_model_is_registered_with_base_metadata() -> None:
    assert Board.__table__ is Base.metadata.tables["boards"]


def test_board_model_has_expected_columns() -> None:
    columns = Board.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "project_id",
        "name",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["project_id"].type, String)
    assert isinstance(columns["name"].type, String)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_board_model_scopes_to_project_with_expected_constraints() -> None:
    table = Board.__table__
    assert isinstance(table, Table)

    foreign_key_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]

    assert any(
        tuple(column.name for column in constraint.columns) == ("project_id",)
        and tuple(element.target_fullname for element in constraint.elements) == ("projects.id",)
        for constraint in foreign_key_constraints
    )
    assert any(index.name == "ix_boards_project_id" for index in table.indexes)


def test_board_model_does_not_introduce_speculative_fields() -> None:
    columns = Board.__table__.columns

    assert "workspace_id" not in columns
    assert "organization_id" not in columns
    assert "description" not in columns
    assert "default_workflow_id" not in columns
    assert "archived_at" not in columns
