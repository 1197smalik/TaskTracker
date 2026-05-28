"""Tests for the ActivityEvent SQLAlchemy model."""

from sqlalchemy import JSON, DateTime, ForeignKeyConstraint, Index, String, Table

from taskmaster_backend.activity.models import ActivityEvent
from taskmaster_backend.db.base import Base


def test_activity_event_model_is_registered_with_base_metadata() -> None:
    assert ActivityEvent.__table__ is Base.metadata.tables["activity_events"]


def test_activity_event_model_has_expected_columns() -> None:
    columns = ActivityEvent.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "actor_id",
        "project_id",
        "entity_type",
        "entity_id",
        "event_type",
        "summary",
        "payload",
        "created_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["actor_id"].type, String)
    assert isinstance(columns["project_id"].type, String)
    assert isinstance(columns["entity_type"].type, String)
    assert isinstance(columns["entity_id"].type, String)
    assert isinstance(columns["event_type"].type, String)
    assert isinstance(columns["summary"].type, String)
    assert isinstance(columns["payload"].type, JSON)
    assert isinstance(columns["created_at"].type, DateTime)


def test_activity_event_model_has_expected_foreign_keys() -> None:
    table = ActivityEvent.__table__
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

    assert foreign_keys[("actor_id",)] == ("users.id",)
    assert foreign_keys[("project_id",)] == ("projects.id",)


def test_activity_event_model_has_expected_indexes() -> None:
    table = ActivityEvent.__table__
    assert isinstance(table, Table)

    index_columns: dict[str, tuple[str, ...]] = {
        str(index.name): tuple(column.name for column in index.columns)
        for index in table.indexes
        if isinstance(index, Index)
    }

    assert index_columns["ix_activity_events_actor_id"] == ("actor_id",)
    assert index_columns["ix_activity_events_project_id"] == ("project_id",)
    assert index_columns["ix_activity_events_entity_type_entity_id_created_at"] == (
        "entity_type",
        "entity_id",
        "created_at",
    )
    assert index_columns["ix_activity_events_project_id_created_at"] == (
        "project_id",
        "created_at",
    )


def test_activity_event_model_does_not_introduce_writer_or_delivery_fields() -> None:
    columns = ActivityEvent.__table__.columns

    assert "audit_log_id" not in columns
    assert "event_outbox_id" not in columns
    assert "notification_id" not in columns
    assert "websocket_delivery_id" not in columns
    assert "read_at" not in columns
