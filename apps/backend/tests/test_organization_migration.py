"""Tests for the organizations table Alembic revision."""

from pathlib import Path

from alembic_test_utils import load_script_directory


def test_organizations_table_revision_is_registered() -> None:
    script_directory = load_script_directory()

    revision = script_directory.get_revision("0003_create_organizations_table")

    assert revision is not None
    assert revision.down_revision == "0002_create_users_table"


def test_organizations_table_revision_script_mentions_expected_columns() -> None:
    script_directory = load_script_directory()
    revision = script_directory.get_revision("0003_create_organizations_table")
    assert revision is not None

    source = Path(revision.path).read_text()

    for expected_fragment in (
        '"organizations"',
        '"id"',
        '"name"',
        '"created_at"',
        '"updated_at"',
        '"ix_organizations_name"',
    ):
        assert expected_fragment in source
