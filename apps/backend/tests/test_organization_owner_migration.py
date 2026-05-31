"""Tests for the organization ownership Alembic revision."""

from pathlib import Path

from alembic_test_utils import load_script_directory


def test_organization_owner_revision_is_registered() -> None:
    script_directory = load_script_directory()

    revision = script_directory.get_revision("0015_add_organization_owner_user_id")

    assert revision is not None
    assert revision.down_revision == "0014_add_workflow_state_position"


def test_organization_owner_revision_adds_owner_column_and_backfill_logic() -> None:
    script_directory = load_script_directory()
    revision = script_directory.get_revision("0015_add_organization_owner_user_id")
    assert revision is not None

    source = Path(revision.path).read_text()

    for expected_fragment in (
        '"organizations"',
        '"owner_user_id"',
        '"ix_organizations_owner_user_id"',
        '"fk_organizations_owner_user_id_users"',
        "SELECT id FROM users",
        "WHERE is_active = true",
        "ORDER BY created_at ASC, id ASC",
        "UPDATE organizations",
        "SET owner_user_id = :owner_user_id",
        "WHERE owner_user_id IS NULL",
    ):
        assert expected_fragment in source


def test_organization_owner_revision_downgrade_reverses_schema_changes() -> None:
    script_directory = load_script_directory()
    revision = script_directory.get_revision("0015_add_organization_owner_user_id")
    assert revision is not None

    source = Path(revision.path).read_text()

    constraint_drop = source.index('batch_op.drop_constraint(')
    index_drop = source.index('batch_op.drop_index("ix_organizations_owner_user_id")')
    column_drop = source.index('batch_op.drop_column("owner_user_id")')

    assert constraint_drop < index_drop < column_drop
