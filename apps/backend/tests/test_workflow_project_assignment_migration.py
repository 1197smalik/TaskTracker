"""Tests for the workflow project assignment Alembic revision."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_workflow_project_assignment_revision_is_registered() -> None:
    config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(config)

    revision = script_directory.get_revision("0012_assign_workflows_to_projects")

    assert revision is not None
    assert revision.down_revision == "0011_create_workflow_tables"


def test_workflow_project_assignment_revision_mentions_expected_schema() -> None:
    config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(config)
    revision = script_directory.get_revision("0012_assign_workflows_to_projects")
    assert revision is not None

    source = Path(revision.path).read_text()

    for expected_fragment in (
        '"workflow_assignments"',
        '"id"',
        '"project_id"',
        '"workflow_definition_id"',
        '"created_at"',
        '"updated_at"',
        '"projects.id"',
        '"workflow_definitions.id"',
        '"uq_workflow_assignments_project_id"',
        '"ix_workflow_assignments_project_id"',
        '"ix_workflow_assignments_workflow_definition_id"',
        '"ix_workflow_assignments_project_id_workflow_definition_id"',
    ):
        assert expected_fragment in source
