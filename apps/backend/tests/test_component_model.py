"""Tests for the Component SQLAlchemy model."""

from sqlalchemy import DateTime, ForeignKeyConstraint, String, Table

from taskmaster_backend.db.base import Base
from taskmaster_backend.projects.models import Component


def test_component_model_is_registered_with_base_metadata() -> None:
    assert Component.__table__ is Base.metadata.tables["components"]


def test_component_model_has_expected_columns() -> None:
    columns = Component.__table__.columns

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


def test_component_model_scopes_to_project_with_expected_constraints() -> None:
    table = Component.__table__
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
    assert any(index.name == "ix_components_project_id" for index in table.indexes)


def test_component_model_does_not_introduce_speculative_fields() -> None:
    columns = Component.__table__.columns

    assert "workspace_id" not in columns
    assert "organization_id" not in columns
    assert "owner_id" not in columns
    assert "lifecycle_state" not in columns
    assert "automation_metadata" not in columns
    assert "external_sync_id" not in columns
