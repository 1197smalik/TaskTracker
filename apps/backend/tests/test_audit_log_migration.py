"""Tests for the audit_logs table Alembic revision."""

from pathlib import Path

from alembic_test_utils import load_script_directory


def test_audit_logs_table_revision_is_registered() -> None:
    script_directory = load_script_directory()

    revision = script_directory.get_revision("0013_create_audit_logs_table")

    assert revision is not None
    assert revision.down_revision == "0012_assign_workflows_to_projects"


def test_audit_logs_table_revision_script_mentions_expected_schema() -> None:
    script_directory = load_script_directory()
    revision = script_directory.get_revision("0013_create_audit_logs_table")
    assert revision is not None

    source = Path(revision.path).read_text()

    for expected_fragment in (
        '"audit_logs"',
        '"id"',
        '"actor_id"',
        '"actor_type"',
        '"organization_id"',
        '"workspace_id"',
        '"project_id"',
        '"entity_type"',
        '"entity_id"',
        '"action"',
        '"before_summary"',
        '"after_summary"',
        '"diff_reference"',
        '"ip_address"',
        '"user_agent"',
        '"correlation_id"',
        '"created_at"',
        '"users.id"',
        '"organizations.id"',
        '"workspaces.id"',
        '"projects.id"',
        '"ix_audit_logs_actor_id"',
        '"ix_audit_logs_actor_id_created_at"',
        '"ix_audit_logs_entity_type_entity_id_created_at"',
        '"ix_audit_logs_action_created_at"',
        '"ix_audit_logs_organization_id"',
        '"ix_audit_logs_organization_id_created_at"',
        '"ix_audit_logs_workspace_id"',
        '"ix_audit_logs_workspace_id_created_at"',
        '"ix_audit_logs_project_id"',
        '"ix_audit_logs_project_id_created_at"',
    ):
        assert expected_fragment in source
