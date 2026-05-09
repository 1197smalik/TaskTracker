"""Tests for the permissions table Alembic revision."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_permissions_table_revision_is_registered() -> None:
    config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(config)

    revision = script_directory.get_revision("0006_create_permissions_table")

    assert revision is not None
    assert revision.down_revision == "0005_create_roles_table"


def test_permissions_table_revision_script_mentions_expected_columns() -> None:
    config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(config)
    revision = script_directory.get_revision("0006_create_permissions_table")
    assert revision is not None

    source = Path(revision.path).read_text()

    for expected_fragment in (
        '"permissions"',
        '"id"',
        '"code"',
        '"created_at"',
        '"updated_at"',
        '"uq_permissions_code"',
        '"ix_permissions_code"',
    ):
        assert expected_fragment in source
