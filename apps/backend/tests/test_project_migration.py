"""Tests for the projects table Alembic revision."""

from pathlib import Path

from alembic_test_utils import load_script_directory


def test_projects_table_revision_is_registered() -> None:
    script_directory = load_script_directory()

    revision = script_directory.get_revision("0007_create_projects_table")

    assert revision is not None
    assert revision.down_revision == "0006_create_permissions_table"


def test_projects_table_revision_script_mentions_expected_columns() -> None:
    script_directory = load_script_directory()
    revision = script_directory.get_revision("0007_create_projects_table")
    assert revision is not None

    source = Path(revision.path).read_text()

    for expected_fragment in (
        '"projects"',
        '"id"',
        '"workspace_id"',
        '"key"',
        '"name"',
        '"created_at"',
        '"updated_at"',
        '"workspaces.id"',
        '"uq_projects_workspace_id_key"',
        '"ix_projects_workspace_id"',
        '"ix_projects_workspace_id_key"',
    ):
        assert expected_fragment in source
