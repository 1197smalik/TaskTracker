"""Tests for the workspaces table Alembic revision."""

from pathlib import Path

from alembic_test_utils import load_script_directory


def test_workspaces_table_revision_is_registered() -> None:
    script_directory = load_script_directory()

    revision = script_directory.get_revision("0004_create_workspaces_table")

    assert revision is not None
    assert revision.down_revision == "0003_create_organizations_table"


def test_workspaces_table_revision_script_mentions_expected_columns() -> None:
    script_directory = load_script_directory()
    revision = script_directory.get_revision("0004_create_workspaces_table")
    assert revision is not None

    source = Path(revision.path).read_text()

    for expected_fragment in (
        '"workspaces"',
        '"id"',
        '"organization_id"',
        '"name"',
        '"created_at"',
        '"updated_at"',
        '"organizations.id"',
        '"ix_workspaces_organization_id"',
        '"ix_workspaces_name"',
    ):
        assert expected_fragment in source
