"""Tests for the Identity workspace SQLAlchemy model."""

from sqlalchemy import DateTime, ForeignKeyConstraint, String, Table

from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Workspace


def test_workspace_model_is_registered_with_base_metadata() -> None:
    assert Workspace.__table__ is Base.metadata.tables["workspaces"]


def test_workspace_model_has_expected_columns() -> None:
    columns = Workspace.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "organization_id",
        "name",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["organization_id"].type, String)
    assert isinstance(columns["name"].type, String)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_workspace_model_scopes_to_organization_with_expected_indexes() -> None:
    table = Workspace.__table__
    assert isinstance(table, Table)

    foreign_key_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]

    assert any(
        tuple(column.name for column in constraint.columns) == ("organization_id",)
        and tuple(element.target_fullname for element in constraint.elements)
        == ("organizations.id",)
        for constraint in foreign_key_constraints
    )
    assert any(index.name == "ix_workspaces_organization_id" for index in table.indexes)
    assert any(index.name == "ix_workspaces_name" for index in table.indexes)


def test_workspace_model_does_not_introduce_speculative_fields() -> None:
    columns = Workspace.__table__.columns

    assert "slug" not in columns
    assert "billing_email" not in columns
    assert "feature_flags" not in columns
