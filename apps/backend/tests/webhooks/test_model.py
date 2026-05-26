"""Tests for the WebhookEndpoint SQLAlchemy model."""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, DateTime, ForeignKeyConstraint, String, Table

from taskmaster_backend.db.base import Base
from taskmaster_backend.integrations.models import WebhookEndpoint


def test_webhook_endpoint_model_is_registered_with_base_metadata() -> None:
    assert WebhookEndpoint.__table__ is Base.metadata.tables["webhook_endpoints"]


def test_webhook_endpoint_model_has_expected_columns() -> None:
    columns = WebhookEndpoint.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "organization_id",
        "workspace_id",
        "url",
        "description",
        "event_types",
        "project_filters",
        "is_active",
        "secret_hash",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["organization_id"].type, String)
    assert isinstance(columns["workspace_id"].type, String)
    assert isinstance(columns["url"].type, String)
    assert isinstance(columns["description"].type, String)
    assert isinstance(columns["event_types"].type, JSON)
    assert isinstance(columns["project_filters"].type, JSON)
    assert isinstance(columns["is_active"].type, Boolean)
    assert isinstance(columns["secret_hash"].type, String)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_webhook_endpoint_model_has_expected_foreign_keys() -> None:
    table = WebhookEndpoint.__table__
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
    assert foreign_keys[("workspace_id",)] == ("workspaces.id",)


def test_webhook_endpoint_model_has_scope_indexes() -> None:
    table = WebhookEndpoint.__table__
    assert isinstance(table, Table)

    assert any(index.name == "ix_webhook_endpoints_organization_id" for index in table.indexes)
    assert any(index.name == "ix_webhook_endpoints_workspace_id" for index in table.indexes)


def test_webhook_endpoint_model_does_not_implement_later_webhook_behaviors() -> None:
    columns = WebhookEndpoint.__table__.columns

    assert "secret" not in columns
    assert "delivery_id" not in columns
    assert "last_delivery_status" not in columns
    assert "retry_count" not in columns
    assert "next_attempt_at" not in columns
