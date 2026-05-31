"""Tests for the Identity organization SQLAlchemy model."""

from sqlalchemy import DateTime, ForeignKeyConstraint, String, Table, UniqueConstraint

from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization


def test_organization_model_is_registered_with_base_metadata() -> None:
    assert Organization.__table__ is Base.metadata.tables["organizations"]


def test_organization_model_has_expected_columns() -> None:
    columns = Organization.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "owner_user_id",
        "name",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["owner_user_id"].type, String)
    assert isinstance(columns["name"].type, String)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_organization_model_indexes_name_and_owner_without_forcing_uniqueness() -> None:
    table = Organization.__table__
    assert isinstance(table, Table)

    foreign_keys = {
        tuple(column.name for column in constraint.columns): tuple(
            element.target_fullname for element in constraint.elements
        )
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }

    assert any(index.name == "ix_organizations_name" for index in table.indexes)
    assert any(index.name == "ix_organizations_owner_user_id" for index in table.indexes)
    assert foreign_keys[("owner_user_id",)] == ("users.id",)
    assert not any(
        isinstance(constraint, UniqueConstraint) for constraint in table.constraints
    )


def test_organization_model_does_not_introduce_speculative_membership_fields() -> None:
    columns = Organization.__table__.columns

    assert "slug" not in columns
    assert "billing_email" not in columns
    assert "subscription_plan" not in columns
    assert "member_count" not in columns
