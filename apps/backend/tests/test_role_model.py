"""Tests for the Identity role SQLAlchemy model."""

from sqlalchemy import DateTime, String, Table, UniqueConstraint

from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Role


def test_role_model_is_registered_with_base_metadata() -> None:
    assert Role.__table__ is Base.metadata.tables["roles"]


def test_role_model_has_expected_columns() -> None:
    columns = Role.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "name",
        "scope",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["name"].type, String)
    assert isinstance(columns["scope"].type, String)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_role_model_enforces_unique_name_per_scope_with_expected_indexes() -> None:
    table = Role.__table__
    assert isinstance(table, Table)

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        constraint.name == "uq_roles_name_scope"
        and tuple(column.name for column in constraint.columns) == ("name", "scope")
        for constraint in unique_constraints
    )
    assert any(index.name == "ix_roles_name" for index in table.indexes)
    assert any(index.name == "ix_roles_scope" for index in table.indexes)


def test_role_model_does_not_introduce_permission_or_membership_fields() -> None:
    columns = Role.__table__.columns

    assert "permission_id" not in columns
    assert "membership_id" not in columns
    assert "organization_id" not in columns
    assert "workspace_id" not in columns
    assert "project_id" not in columns
