"""Tests for the Version SQLAlchemy model."""

from sqlalchemy import DateTime, ForeignKeyConstraint, String, Table, UniqueConstraint

from taskmaster_backend.db.base import Base
from taskmaster_backend.projects.models import Version


def test_version_model_is_registered_with_base_metadata() -> None:
    assert Version.__table__ is Base.metadata.tables["versions"]


def test_version_model_has_expected_columns() -> None:
    columns = Version.__table__.columns

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


def test_version_model_scopes_to_project_with_expected_constraints() -> None:
    table = Version.__table__
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
        constraint.name == "uq_versions_project_id_name"
        and tuple(column.name for column in constraint.columns) == ("project_id", "name")
        for constraint in unique_constraints
    )
    assert any(
        tuple(column.name for column in constraint.columns) == ("project_id",)
        and tuple(element.target_fullname for element in constraint.elements) == ("projects.id",)
        for constraint in foreign_key_constraints
    )
    assert any(index.name == "ix_versions_project_id" for index in table.indexes)
    assert any(index.name == "ix_versions_project_id_name" for index in table.indexes)


def test_version_model_does_not_introduce_speculative_fields() -> None:
    columns = Version.__table__.columns

    assert "workspace_id" not in columns
    assert "organization_id" not in columns
    assert "release_date" not in columns
    assert "deployment_metadata" not in columns
    assert "changelog_content" not in columns
    assert "external_sync_id" not in columns
