"""Tests for the workflow tables Alembic revision."""

from pathlib import Path

from alembic_test_utils import load_script_directory


def test_workflow_tables_revision_is_registered() -> None:
    script_directory = load_script_directory()

    revision = script_directory.get_revision("0011_create_workflow_tables")

    assert revision is not None
    assert revision.down_revision == "0010_add_work_item_parent_relationship"


def test_workflow_tables_revision_script_mentions_expected_schema() -> None:
    script_directory = load_script_directory()
    revision = script_directory.get_revision("0011_create_workflow_tables")
    assert revision is not None

    source = Path(revision.path).read_text()

    for expected_fragment in (
        '"workflow_definitions"',
        '"workflow_states"',
        '"workflow_transitions"',
        '"workflow_transition_rules"',
        '"project_id"',
        '"workflow_definition_id"',
        '"source_state_id"',
        '"target_state_id"',
        '"workflow_transition_id"',
        '"rule_type"',
        '"config"',
        '"version"',
        '"description"',
        '"projects.id"',
        '"workflow_definitions.id"',
        '"workflow_states.id"',
        '"workflow_transitions.id"',
        '"ck_workflow_definitions_version_positive"',
        '"ck_workflow_transitions_distinct_states"',
        '"ck_workflow_transition_rules_type_supported"',
        '"uq_workflow_definitions_project_id_name_version"',
        '"uq_workflow_states_workflow_definition_id_name"',
        '"uq_workflow_transitions_workflow_definition_id_source_target"',
        '"uq_workflow_transition_rules_transition_id_rule_type"',
        '"ix_workflow_definitions_project_id"',
        '"ix_workflow_definitions_project_id_name"',
        '"ix_workflow_states_workflow_definition_id"',
        '"ix_workflow_states_workflow_definition_id_name"',
        '"ix_workflow_transitions_workflow_definition_id"',
        '"ix_workflow_transitions_workflow_definition_id_source_state_id"',
        '"ix_workflow_transitions_workflow_definition_id_target_state_id"',
        '"ix_workflow_transition_rules_workflow_transition_id"',
        '"ix_workflow_transition_rules_transition_id_rule_type"',
    ):
        assert expected_fragment in source


def test_workflow_tables_revision_downgrade_drops_children_before_parents() -> None:
    script_directory = load_script_directory()
    revision = script_directory.get_revision("0011_create_workflow_tables")
    assert revision is not None

    source = Path(revision.path).read_text()

    rules_drop = source.index('op.drop_table("workflow_transition_rules")')
    transitions_drop = source.index('op.drop_table("workflow_transitions")')
    states_drop = source.index('op.drop_table("workflow_states")')
    definitions_drop = source.index('op.drop_table("workflow_definitions")')

    assert rules_drop < transitions_drop < states_drop < definitions_drop
