"""Tests for the Identity permission SQLAlchemy model."""

from sqlalchemy import DateTime, String, Table, UniqueConstraint

from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Permission


def test_permission_model_is_registered_with_base_metadata() -> None:
    assert Permission.__table__ is Base.metadata.tables["permissions"]


def test_permission_model_has_expected_columns() -> None:
    columns = Permission.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "code",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["code"].type, String)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_permission_model_enforces_unique_code_with_expected_index() -> None:
    table = Permission.__table__
    assert isinstance(table, Table)

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        constraint.name == "uq_permissions_code"
        and tuple(column.name for column in constraint.columns) == ("code",)
        for constraint in unique_constraints
    )
    assert any(index.name == "ix_permissions_code" for index in table.indexes)


def test_permission_model_does_not_introduce_role_or_membership_fields() -> None:
    columns = Permission.__table__.columns

    assert "role_id" not in columns
    assert "membership_id" not in columns
    assert "scope" not in columns
    assert "description" not in columns
