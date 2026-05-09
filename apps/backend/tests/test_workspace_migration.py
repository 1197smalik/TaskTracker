"""Tests for the workspaces table Alembic revision."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_workspaces_table_revision_is_registered() -> None:
    config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(config)

    revision = script_directory.get_revision("0004_create_workspaces_table")

    assert revision is not None
    assert revision.down_revision == "0003_create_organizations_table"


def test_workspaces_table_revision_script_mentions_expected_columns() -> None:
    config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(config)
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
