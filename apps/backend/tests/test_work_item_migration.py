"""Tests for the work_items table Alembic revision."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_work_items_table_revision_is_registered() -> None:
    config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(config)

    revision = script_directory.get_revision("0009_create_work_items_table")

    assert revision is not None
    assert revision.down_revision == "0008_create_boards_table"


def test_work_items_table_revision_script_mentions_expected_schema() -> None:
    config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(config)
    revision = script_directory.get_revision("0009_create_work_items_table")
    assert revision is not None

    source = Path(revision.path).read_text()

    for expected_fragment in (
        '"work_items"',
        '"id"',
        '"project_id"',
        '"sprint_id"',
        '"epic_id"',
        '"assignee_id"',
        '"reporter_id"',
        '"current_state_id"',
        '"type"',
        '"status"',
        '"title"',
        '"description"',
        '"priority"',
        '"severity"',
        '"estimate"',
        '"typed_metadata"',
        '"version"',
        '"created_at"',
        '"updated_at"',
        '"projects.id"',
        '"sprints.id"',
        '"epics.id"',
        '"users.id"',
        '"ck_work_items_type_supported"',
        '"ck_work_items_version_positive"',
        '"ix_work_items_project_id"',
        '"ix_work_items_project_id_assignee_id_status"',
        '"ix_work_items_project_id_current_state_id"',
        '"ix_work_items_project_id_id"',
        '"ix_work_items_project_id_sprint_id"',
        '"ix_work_items_project_id_type_priority"',
    ):
        assert expected_fragment in source
