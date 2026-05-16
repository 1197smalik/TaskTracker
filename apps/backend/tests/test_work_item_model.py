"""Tests for the WorkItem SQLAlchemy model."""

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Table,
    Text,
)

from taskmaster_backend.db.base import Base
from taskmaster_backend.work_items.models import WorkItem


def test_work_item_model_is_registered_with_base_metadata() -> None:
    assert WorkItem.__table__ is Base.metadata.tables["work_items"]


def test_work_item_model_has_expected_columns() -> None:
    columns = WorkItem.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "project_id",
        "parent_id",
        "sprint_id",
        "epic_id",
        "assignee_id",
        "reporter_id",
        "current_state_id",
        "type",
        "status",
        "title",
        "description",
        "priority",
        "severity",
        "estimate",
        "typed_metadata",
        "version",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["project_id"].type, String)
    assert isinstance(columns["parent_id"].type, String)
    assert isinstance(columns["sprint_id"].type, String)
    assert isinstance(columns["epic_id"].type, String)
    assert isinstance(columns["assignee_id"].type, String)
    assert isinstance(columns["reporter_id"].type, String)
    assert isinstance(columns["current_state_id"].type, String)
    assert isinstance(columns["type"].type, String)
    assert isinstance(columns["status"].type, String)
    assert isinstance(columns["title"].type, String)
    assert isinstance(columns["description"].type, Text)
    assert isinstance(columns["priority"].type, String)
    assert isinstance(columns["severity"].type, String)
    assert isinstance(columns["estimate"].type, Integer)
    assert isinstance(columns["typed_metadata"].type, JSON)
    assert isinstance(columns["version"].type, Integer)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_work_item_model_has_expected_foreign_keys() -> None:
    table = WorkItem.__table__
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

    assert foreign_keys[("project_id",)] == ("projects.id",)
    assert foreign_keys[("parent_id",)] == ("work_items.id",)
    assert foreign_keys[("sprint_id",)] == ("sprints.id",)
    assert foreign_keys[("epic_id",)] == ("epics.id",)
    assert foreign_keys[("assignee_id",)] == ("users.id",)
    assert foreign_keys[("reporter_id",)] == ("users.id",)
    assert ("current_state_id",) not in foreign_keys


def test_work_item_model_has_project_scoped_indexes_and_constraints() -> None:
    table = WorkItem.__table__
    assert isinstance(table, Table)

    index_columns: dict[str, tuple[str, ...]] = {
        str(index.name): tuple(column.name for column in index.columns)
        for index in table.indexes
        if isinstance(index, Index)
    }
    check_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    ]

    assert index_columns["ix_work_items_project_id"] == ("project_id",)
    assert index_columns["ix_work_items_project_id_id"] == ("project_id", "id")
    assert index_columns["ix_work_items_project_id_parent_id"] == ("project_id", "parent_id")
    assert index_columns["ix_work_items_project_id_current_state_id"] == (
        "project_id",
        "current_state_id",
    )
    assert index_columns["ix_work_items_project_id_assignee_id_status"] == (
        "project_id",
        "assignee_id",
        "status",
    )
    assert index_columns["ix_work_items_project_id_type_priority"] == (
        "project_id",
        "type",
        "priority",
    )
    assert index_columns["ix_work_items_project_id_sprint_id"] == ("project_id", "sprint_id")
    assert any(
        constraint.name == "ck_work_items_type_supported" for constraint in check_constraints
    )
    assert any(
        constraint.name == "ck_work_items_version_positive" for constraint in check_constraints
    )
    assert any(
        constraint.name == "ck_work_items_not_self_parent" for constraint in check_constraints
    )


def test_work_item_model_does_not_introduce_later_story_or_speculative_fields() -> None:
    columns = WorkItem.__table__.columns

    assert "board_id" not in columns
    assert "label_id" not in columns
    assert "component_id" not in columns
    assert "version_id" not in columns
    assert "workflow_definition_id" not in columns
    assert "automation_metadata" not in columns
    assert "ai_metadata" not in columns
    assert "external_sync_id" not in columns
