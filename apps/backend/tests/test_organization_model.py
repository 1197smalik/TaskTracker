"""Tests for the Identity organization SQLAlchemy model."""

from sqlalchemy import DateTime, String, Table

from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization


def test_organization_model_is_registered_with_base_metadata() -> None:
    assert Organization.__table__ is Base.metadata.tables["organizations"]


def test_organization_model_has_expected_columns() -> None:
    columns = Organization.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "name",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["name"].type, String)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_organization_model_indexes_name_without_forcing_uniqueness() -> None:
    table = Organization.__table__
    assert isinstance(table, Table)

    assert any(index.name == "ix_organizations_name" for index in table.indexes)
    assert len(table.constraints) == 1


def test_organization_model_does_not_introduce_speculative_fields() -> None:
    columns = Organization.__table__.columns

    assert "slug" not in columns
    assert "billing_email" not in columns
    assert "subscription_plan" not in columns
