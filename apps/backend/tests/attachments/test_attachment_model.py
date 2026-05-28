"""Tests for the Attachment SQLAlchemy model."""

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Table,
    UniqueConstraint,
)

from taskmaster_backend.collaboration.models import Attachment
from taskmaster_backend.db.base import Base


def test_attachment_model_is_registered_with_base_metadata() -> None:
    assert Attachment.__table__ is Base.metadata.tables["attachments"]


def test_attachment_model_has_expected_columns() -> None:
    columns = Attachment.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "work_item_id",
        "uploader_id",
        "storage_key",
        "file_name",
        "content_type",
        "size_bytes",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["work_item_id"].type, String)
    assert isinstance(columns["uploader_id"].type, String)
    assert isinstance(columns["storage_key"].type, String)
    assert isinstance(columns["file_name"].type, String)
    assert isinstance(columns["content_type"].type, String)
    assert isinstance(columns["size_bytes"].type, Integer)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_attachment_model_has_expected_relationship_constraints() -> None:
    table = Attachment.__table__
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
    assert foreign_keys[("uploader_id",)] == ("users.id",)


def test_attachment_model_has_expected_indexes_and_constraints() -> None:
    table = Attachment.__table__
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

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    assert index_columns["ix_attachments_uploader_id"] == ("uploader_id",)
    assert index_columns["ix_attachments_work_item_id_created_at"] == (
        "work_item_id",
        "created_at",
    )
    assert any(
        tuple(column.name for column in constraint.columns) == ("storage_key",)
        for constraint in unique_constraints
    )
    assert any(
        constraint.name == "ck_attachments_size_bytes_non_negative"
        for constraint in check_constraints
    )


def test_attachment_model_does_not_introduce_storage_or_upload_behavior() -> None:
    columns = Attachment.__table__.columns

    assert "upload_url" not in columns
    assert "download_url" not in columns
    assert "storage_provider" not in columns
    assert "scan_status" not in columns
    assert "deleted_at" not in columns
    assert "visibility" not in columns
