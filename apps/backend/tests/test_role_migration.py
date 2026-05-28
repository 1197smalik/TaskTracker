"""Tests for the roles table Alembic revision."""

from pathlib import Path

from alembic_test_utils import load_script_directory


def test_roles_table_revision_is_registered() -> None:
    script_directory = load_script_directory()

    revision = script_directory.get_revision("0005_create_roles_table")

    assert revision is not None
    assert revision.down_revision == "0004_create_workspaces_table"


def test_roles_table_revision_script_mentions_expected_columns() -> None:
    script_directory = load_script_directory()
    revision = script_directory.get_revision("0005_create_roles_table")
    assert revision is not None

    source = Path(revision.path).read_text()

    for expected_fragment in (
        '"roles"',
        '"id"',
        '"name"',
        '"scope"',
        '"created_at"',
        '"updated_at"',
        '"uq_roles_name_scope"',
        '"ix_roles_name"',
        '"ix_roles_scope"',
    ):
        assert expected_fragment in source
