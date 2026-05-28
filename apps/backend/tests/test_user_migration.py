"""Tests for the users table Alembic revision."""

from pathlib import Path

from alembic_test_utils import load_script_directory


def test_users_table_revision_is_registered() -> None:
    script_directory = load_script_directory()

    revision = script_directory.get_revision("0002_create_users_table")

    assert revision is not None
    assert revision.down_revision == "0001_baseline"


def test_users_table_revision_script_mentions_expected_columns() -> None:
    script_directory = load_script_directory()
    revision = script_directory.get_revision("0002_create_users_table")
    assert revision is not None

    source = Path(revision.path).read_text()

    for expected_fragment in (
        '"users"',
        '"email"',
        '"password_hash"',
        '"is_active"',
        '"created_at"',
        '"updated_at"',
        '"uq_users_email"',
        '"ix_users_email"',
    ):
        assert expected_fragment in source
