"""Tests for the Identity user SQLAlchemy model."""

from sqlalchemy import Boolean, DateTime, String, Table, UniqueConstraint

from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import User


def test_user_model_is_registered_with_base_metadata() -> None:
    assert User.__table__ is Base.metadata.tables["users"]


def test_user_model_has_expected_columns() -> None:
    columns = User.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "email",
        "password_hash",
        "is_active",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["email"].type, String)
    assert isinstance(columns["password_hash"].type, String)
    assert isinstance(columns["is_active"].type, Boolean)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_user_model_has_unique_email_constraint() -> None:
    table = User.__table__
    assert isinstance(table, Table)

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        constraint.name == "uq_users_email"
        and tuple(column.name for column in constraint.columns) == ("email",)
        for constraint in unique_constraints
    )


def test_user_model_does_not_store_plaintext_password_field() -> None:
    assert "password" not in User.__table__.columns
