"""Tests for API token SQLAlchemy model metadata."""

from __future__ import annotations

from sqlalchemy import JSON, DateTime, ForeignKeyConstraint, String, Table, UniqueConstraint

from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import ApiToken


def test_api_token_model_is_registered_with_base_metadata() -> None:
    assert ApiToken.__table__ is Base.metadata.tables["api_tokens"]


def test_api_token_model_has_expected_columns() -> None:
    columns = ApiToken.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "organization_id",
        "name",
        "token_hash",
        "scopes",
        "expires_at",
        "revoked_at",
        "last_used_at",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["organization_id"].type, String)
    assert isinstance(columns["name"].type, String)
    assert isinstance(columns["token_hash"].type, String)
    assert isinstance(columns["scopes"].type, JSON)
    assert isinstance(columns["expires_at"].type, DateTime)
    assert isinstance(columns["revoked_at"].type, DateTime)
    assert isinstance(columns["last_used_at"].type, DateTime)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_api_token_model_is_organization_scoped() -> None:
    table = ApiToken.__table__
    assert isinstance(table, Table)

    foreign_key_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    foreign_keys = {
        tuple(column.name for column in constraint.columns): tuple(
            element.target_fullname for element in constraint.elements
        )
        for constraint in foreign_key_constraints
    }

    assert foreign_keys[("organization_id",)] == ("organizations.id",)
    assert any(index.name == "ix_api_tokens_organization_id" for index in table.indexes)


def test_api_token_model_enforces_unique_token_hash() -> None:
    table = ApiToken.__table__
    assert isinstance(table, Table)

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        constraint.name == "uq_api_tokens_token_hash"
        and tuple(column.name for column in constraint.columns) == ("token_hash",)
        for constraint in unique_constraints
    )
    assert any(index.name == "ix_api_tokens_token_hash" for index in table.indexes)


def test_api_token_model_does_not_store_raw_token_or_implement_management_state() -> None:
    columns = ApiToken.__table__.columns

    assert "raw_token" not in columns
    assert "token" not in columns
    assert "plain_text_token" not in columns
    assert "created_by_user_id" not in columns
    assert "deleted_at" not in columns
