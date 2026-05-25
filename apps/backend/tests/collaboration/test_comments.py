"""Tests for the Comment SQLAlchemy model."""

from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, Index, String, Table, Text

from taskmaster_backend.collaboration.models import Comment
from taskmaster_backend.db.base import Base


def test_comment_model_is_registered_with_base_metadata() -> None:
    assert Comment.__table__ is Base.metadata.tables["comments"]


def test_comment_model_has_expected_columns() -> None:
    columns = Comment.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "work_item_id",
        "author_id",
        "body",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["work_item_id"].type, String)
    assert isinstance(columns["author_id"].type, String)
    assert isinstance(columns["body"].type, Text)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_comment_model_has_expected_relationship_constraints() -> None:
    table = Comment.__table__
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

    assert foreign_keys[("work_item_id",)] == ("work_items.id",)
    assert foreign_keys[("author_id",)] == ("users.id",)


def test_comment_model_has_expected_indexes_and_constraints() -> None:
    table = Comment.__table__
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

    assert index_columns["ix_comments_author_id"] == ("author_id",)
    assert index_columns["ix_comments_work_item_id_created_at"] == (
        "work_item_id",
        "created_at",
    )
    assert any(constraint.name == "ck_comments_body_non_empty" for constraint in check_constraints)


def test_comment_model_does_not_introduce_later_story_fields() -> None:
    columns = Comment.__table__.columns

    assert "mentions" not in columns
    assert "attachment_id" not in columns
    assert "activity_event_id" not in columns
    assert "notification_id" not in columns
    assert "rendered_body" not in columns
    assert "visibility" not in columns
    assert "deleted_at" not in columns
