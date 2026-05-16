"""Tests for the Label SQLAlchemy model."""

from sqlalchemy import DateTime, ForeignKeyConstraint, String, Table

from taskmaster_backend.db.base import Base
from taskmaster_backend.projects.models import Label


def test_label_model_is_registered_with_base_metadata() -> None:
    assert Label.__table__ is Base.metadata.tables["labels"]


def test_label_model_has_expected_columns() -> None:
    columns = Label.__table__.columns

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


def test_label_model_scopes_to_project_with_expected_constraints() -> None:
    table = Label.__table__
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
    assert any(index.name == "ix_labels_project_id" for index in table.indexes)


def test_label_model_does_not_introduce_speculative_fields() -> None:
    columns = Label.__table__.columns

    assert "workspace_id" not in columns
    assert "organization_id" not in columns
    assert "color" not in columns
    assert "automation_metadata" not in columns
    assert "external_sync_id" not in columns
