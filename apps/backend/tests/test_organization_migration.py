"""Tests for the organizations table Alembic revision."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_organizations_table_revision_is_registered() -> None:
    config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(config)

    revision = script_directory.get_revision("0003_create_organizations_table")

    assert revision is not None
    assert revision.down_revision == "0002_create_users_table"


def test_organizations_table_revision_script_mentions_expected_columns() -> None:
    config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(config)
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
