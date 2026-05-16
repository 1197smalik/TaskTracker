"""Tests for the Project SQLAlchemy model."""

from sqlalchemy import DateTime, ForeignKeyConstraint, String, Table, UniqueConstraint

from taskmaster_backend.db.base import Base
from taskmaster_backend.projects.models import Project


def test_project_model_is_registered_with_base_metadata() -> None:
    assert Project.__table__ is Base.metadata.tables["projects"]


def test_project_model_has_expected_columns() -> None:
    columns = Project.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "workspace_id",
        "key",
        "name",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["workspace_id"].type, String)
    assert isinstance(columns["key"].type, String)
    assert isinstance(columns["name"].type, String)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_project_model_scopes_to_workspace_with_expected_constraints() -> None:
    table = Project.__table__
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

    assert any(
        constraint.name == "uq_projects_workspace_id_key"
        and tuple(column.name for column in constraint.columns) == ("workspace_id", "key")
        for constraint in unique_constraints
    )
    assert any(
        tuple(column.name for column in constraint.columns) == ("workspace_id",)
        and tuple(element.target_fullname for element in constraint.elements) == ("workspaces.id",)
        for constraint in foreign_key_constraints
    )
    assert any(index.name == "ix_projects_workspace_id" for index in table.indexes)
    assert any(index.name == "ix_projects_workspace_id_key" for index in table.indexes)


def test_project_model_does_not_introduce_speculative_fields() -> None:
    columns = Project.__table__.columns

    assert "organization_id" not in columns
    assert "billing_plan" not in columns
    assert "external_sync_id" not in columns
    assert "ai_metadata" not in columns
