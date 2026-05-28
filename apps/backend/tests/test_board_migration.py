"""Tests for the boards table Alembic revision."""

from pathlib import Path

from alembic_test_utils import load_script_directory


def test_boards_table_revision_is_registered() -> None:
    script_directory = load_script_directory()

    revision = script_directory.get_revision("0008_create_boards_table")

    assert revision is not None
    assert revision.down_revision == "0007_create_projects_table"


def test_boards_table_revision_script_mentions_expected_columns() -> None:
    script_directory = load_script_directory()
    revision = script_directory.get_revision("0008_create_boards_table")
    assert revision is not None

    source = Path(revision.path).read_text()

    for expected_fragment in (
        '"boards"',
        '"id"',
        '"project_id"',
        '"name"',
        '"created_at"',
        '"updated_at"',
        '"projects.id"',
        '"ix_boards_project_id"',
    ):
        assert expected_fragment in source
