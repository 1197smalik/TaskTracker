"""Tests for the Notification SQLAlchemy model."""

from sqlalchemy import JSON, DateTime, ForeignKeyConstraint, Index, String, Table, Text

from taskmaster_backend.collaboration.models import Notification
from taskmaster_backend.db.base import Base


def test_notification_model_is_registered_with_base_metadata() -> None:
    assert Notification.__table__ is Base.metadata.tables["notifications"]


def test_notification_model_has_expected_columns() -> None:
    columns = Notification.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "recipient_id",
        "organization_id",
        "workspace_id",
        "project_id",
        "notification_type",
        "title",
        "body",
        "entity_type",
        "entity_id",
        "payload",
        "read_at",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["recipient_id"].type, String)
    assert isinstance(columns["organization_id"].type, String)
    assert isinstance(columns["workspace_id"].type, String)
    assert isinstance(columns["project_id"].type, String)
    assert isinstance(columns["notification_type"].type, String)
    assert isinstance(columns["title"].type, String)
    assert isinstance(columns["body"].type, Text)
    assert isinstance(columns["entity_type"].type, String)
    assert isinstance(columns["entity_id"].type, String)
    assert isinstance(columns["payload"].type, JSON)
    assert isinstance(columns["read_at"].type, DateTime)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_notification_model_has_expected_foreign_keys() -> None:
    table = Notification.__table__
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

    assert foreign_keys[("recipient_id",)] == ("users.id",)
    assert foreign_keys[("organization_id",)] == ("organizations.id",)
    assert foreign_keys[("workspace_id",)] == ("workspaces.id",)
    assert foreign_keys[("project_id",)] == ("projects.id",)


def test_notification_model_has_expected_indexes() -> None:
    table = Notification.__table__
    assert isinstance(table, Table)

    index_columns: dict[str, tuple[str, ...]] = {
        str(index.name): tuple(column.name for column in index.columns)
        for index in table.indexes
        if isinstance(index, Index)
    }

    assert index_columns["ix_notifications_recipient_id_read_at_created_at"] == (
        "recipient_id",
        "read_at",
        "created_at",
    )
    assert index_columns["ix_notifications_entity_type_entity_id_created_at"] == (
        "entity_type",
        "entity_id",
        "created_at",
    )
    assert index_columns["ix_notifications_organization_id"] == ("organization_id",)
    assert index_columns["ix_notifications_workspace_id"] == ("workspace_id",)
    assert index_columns["ix_notifications_project_id"] == ("project_id",)


def test_notification_model_does_not_introduce_delivery_or_endpoint_fields() -> None:
    columns = Notification.__table__.columns

    assert "websocket_delivery_id" not in columns
    assert "webhook_delivery_id" not in columns
    assert "delivery_status" not in columns
    assert "retry_count" not in columns
    assert "sent_at" not in columns
    assert "archived_at" not in columns
