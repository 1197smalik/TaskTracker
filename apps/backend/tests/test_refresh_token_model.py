"""Tests for the Identity refresh token SQLAlchemy model."""

from sqlalchemy import DateTime, ForeignKeyConstraint, String, Table, UniqueConstraint

from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import RefreshToken


def test_refresh_token_model_is_registered_with_base_metadata() -> None:
    assert RefreshToken.__table__ is Base.metadata.tables["refresh_tokens"]


def test_refresh_token_model_has_expected_columns() -> None:
    columns = RefreshToken.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "user_id",
        "token_hash",
        "expires_at",
        "revoked_at",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["user_id"].type, String)
    assert isinstance(columns["token_hash"].type, String)
    assert isinstance(columns["expires_at"].type, DateTime)
    assert isinstance(columns["revoked_at"].type, DateTime)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_refresh_token_model_enforces_hash_storage_and_user_fk() -> None:
    table = RefreshToken.__table__
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
        constraint.name == "uq_refresh_tokens_token_hash"
        and tuple(column.name for column in constraint.columns) == ("token_hash",)
        for constraint in unique_constraints
    )
    assert any(
        tuple(column.name for column in constraint.columns) == ("user_id",)
        and tuple(element.target_fullname for element in constraint.elements) == ("users.id",)
        for constraint in foreign_key_constraints
    )
    assert any(index.name == "ix_refresh_tokens_user_id" for index in table.indexes)
    assert any(index.name == "ix_refresh_tokens_token_hash" for index in table.indexes)


def test_refresh_token_model_does_not_store_plaintext_token_or_speculative_fields() -> None:
    columns = RefreshToken.__table__.columns

    assert "token" not in columns
    assert "raw_token" not in columns
    assert "device_id" not in columns
    assert "session_id" not in columns
