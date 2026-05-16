"""Tests for the Sprint SQLAlchemy model."""

from sqlalchemy import DateTime, ForeignKeyConstraint, String, Table

from taskmaster_backend.db.base import Base
from taskmaster_backend.projects.models import Sprint


def test_sprint_model_is_registered_with_base_metadata() -> None:
    assert Sprint.__table__ is Base.metadata.tables["sprints"]


def test_sprint_model_has_expected_columns() -> None:
    columns = Sprint.__table__.columns

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


def test_sprint_model_scopes_to_project_with_expected_constraints() -> None:
    table = Sprint.__table__
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
    assert any(index.name == "ix_sprints_project_id" for index in table.indexes)


def test_sprint_model_does_not_introduce_speculative_fields() -> None:
    columns = Sprint.__table__.columns

    assert "workspace_id" not in columns
    assert "organization_id" not in columns
    assert "start_date" not in columns
    assert "end_date" not in columns
    assert "velocity" not in columns
    assert "status" not in columns
