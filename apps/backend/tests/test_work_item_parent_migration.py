"""Tests for the work item parent relationship Alembic revision."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_work_item_parent_relationship_revision_is_registered() -> None:
    config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(config)

    revision = script_directory.get_revision("0010_add_work_item_parent_relationship")

    assert revision is not None
    assert revision.down_revision == "0009_create_work_items_table"


def test_work_item_parent_relationship_revision_mentions_expected_schema() -> None:
    config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(config)
    revision = script_directory.get_revision("0010_add_work_item_parent_relationship")
    assert revision is not None

    source = Path(revision.path).read_text()

    for expected_fragment in (
        '"work_items"',
        '"parent_id"',
        '"fk_work_items_parent_id_work_items"',
        '"ck_work_items_not_self_parent"',
        '"ix_work_items_project_id_parent_id"',
    ):
        assert expected_fragment in source
