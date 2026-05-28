"""Tests for the workflow state position Alembic revision."""

from pathlib import Path

from alembic_test_utils import load_script_directory


def test_workflow_state_position_revision_is_registered() -> None:
    script_directory = load_script_directory()

    revision = script_directory.get_revision("0014_add_workflow_state_position")

    assert revision is not None
    assert revision.down_revision == "0013_create_audit_logs_table"


def test_workflow_state_position_revision_adds_minimal_ordering_field() -> None:
    script_directory = load_script_directory()
    revision = script_directory.get_revision("0014_add_workflow_state_position")
    assert revision is not None

    source = Path(revision.path).read_text()

    for expected_fragment in (
        '"workflow_states"',
        '"position"',
        "sa.Integer()",
        'server_default="0"',
        '"ck_workflow_states_position_non_negative"',
        '"position >= 0"',
        '"ix_workflow_states_workflow_definition_id_position"',
        '["workflow_definition_id", "position"]',
    ):
        assert expected_fragment in source


def test_workflow_state_position_revision_keeps_scope_to_state_ordering() -> None:
    script_directory = load_script_directory()
    revision = script_directory.get_revision("0014_add_workflow_state_position")
    assert revision is not None

    source = Path(revision.path).read_text()

    assert "board_columns" not in source
    assert "workflow_transitions" not in source
    assert "allowed_transition" not in source


def test_workflow_state_position_revision_downgrade_reverses_schema_changes() -> None:
    script_directory = load_script_directory()
    revision = script_directory.get_revision("0014_add_workflow_state_position")
    assert revision is not None

    source = Path(revision.path).read_text()

    index_drop = source.index(
        'batch_op.drop_index("ix_workflow_states_workflow_definition_id_position")'
    )
    constraint_drop = source.index(
        'batch_op.drop_constraint("ck_workflow_states_position_non_negative"'
    )
    column_drop = source.index('batch_op.drop_column("position")')

    assert index_drop < constraint_drop < column_drop
