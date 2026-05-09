"""Tests for the users table Alembic revision."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_users_table_revision_is_registered() -> None:
    config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(config)

    revision = script_directory.get_revision("0002_create_users_table")

    assert revision is not None
    assert revision.down_revision == "0001_baseline"


def test_users_table_revision_script_mentions_expected_columns() -> None:
    config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(config)
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
