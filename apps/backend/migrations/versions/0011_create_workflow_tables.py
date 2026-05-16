"""Create workflow tables."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0011_create_workflow_tables"
down_revision = "0010_add_work_item_parent_relationship"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_definitions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_workflow_definitions_version_positive",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "name",
            "version",
            name="uq_workflow_definitions_project_id_name_version",
        ),
    )
    op.create_index(
        "ix_workflow_definitions_project_id",
        "workflow_definitions",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_workflow_definitions_project_id_name",
        "workflow_definitions",
        ["project_id", "name"],
        unique=False,
    )

    op.create_table(
        "workflow_states",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workflow_definition_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workflow_definition_id"],
            ["workflow_definitions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workflow_definition_id",
            "name",
            name="uq_workflow_states_workflow_definition_id_name",
        ),
    )
    op.create_index(
        "ix_workflow_states_workflow_definition_id",
        "workflow_states",
        ["workflow_definition_id"],
        unique=False,
    )
    op.create_index(
        "ix_workflow_states_workflow_definition_id_name",
        "workflow_states",
        ["workflow_definition_id", "name"],
        unique=False,
    )

    op.create_table(
        "workflow_transitions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workflow_definition_id", sa.String(length=36), nullable=False),
        sa.Column("source_state_id", sa.String(length=36), nullable=False),
        sa.Column("target_state_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "source_state_id != target_state_id",
            name="ck_workflow_transitions_distinct_states",
        ),
        sa.ForeignKeyConstraint(
            ["source_state_id"],
            ["workflow_states.id"],
        ),
        sa.ForeignKeyConstraint(
            ["target_state_id"],
            ["workflow_states.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workflow_definition_id"],
            ["workflow_definitions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workflow_definition_id",
            "source_state_id",
            "target_state_id",
            name="uq_workflow_transitions_workflow_definition_id_source_target",
        ),
    )
    op.create_index(
        "ix_workflow_transitions_workflow_definition_id",
        "workflow_transitions",
        ["workflow_definition_id"],
        unique=False,
    )
    op.create_index(
        "ix_workflow_transitions_workflow_definition_id_source_state_id",
        "workflow_transitions",
        ["workflow_definition_id", "source_state_id"],
        unique=False,
    )
    op.create_index(
        "ix_workflow_transitions_workflow_definition_id_target_state_id",
        "workflow_transitions",
        ["workflow_definition_id", "target_state_id"],
        unique=False,
    )

    op.create_table(
        "workflow_transition_rules",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workflow_transition_id", sa.String(length=36), nullable=False),
        sa.Column("rule_type", sa.String(length=64), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "rule_type IN ("
            "'required_fields', "
            "'allowed_roles', "
            "'assignee_reporter', "
            "'parent_child_completion', "
            "'comment_required'"
            ")",
            name="ck_workflow_transition_rules_type_supported",
        ),
        sa.ForeignKeyConstraint(
            ["workflow_transition_id"],
            ["workflow_transitions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workflow_transition_id",
            "rule_type",
            name="uq_workflow_transition_rules_transition_id_rule_type",
        ),
    )
    op.create_index(
        "ix_workflow_transition_rules_workflow_transition_id",
        "workflow_transition_rules",
        ["workflow_transition_id"],
        unique=False,
    )
    op.create_index(
        "ix_workflow_transition_rules_transition_id_rule_type",
        "workflow_transition_rules",
        ["workflow_transition_id", "rule_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workflow_transition_rules_transition_id_rule_type",
        table_name="workflow_transition_rules",
    )
    op.drop_index(
        "ix_workflow_transition_rules_workflow_transition_id",
        table_name="workflow_transition_rules",
    )
    op.drop_table("workflow_transition_rules")

    op.drop_index(
        "ix_workflow_transitions_workflow_definition_id_target_state_id",
        table_name="workflow_transitions",
    )
    op.drop_index(
        "ix_workflow_transitions_workflow_definition_id_source_state_id",
        table_name="workflow_transitions",
    )
    op.drop_index(
        "ix_workflow_transitions_workflow_definition_id",
        table_name="workflow_transitions",
    )
    op.drop_table("workflow_transitions")

    op.drop_index(
        "ix_workflow_states_workflow_definition_id_name",
        table_name="workflow_states",
    )
    op.drop_index(
        "ix_workflow_states_workflow_definition_id",
        table_name="workflow_states",
    )
    op.drop_table("workflow_states")

    op.drop_index(
        "ix_workflow_definitions_project_id_name",
        table_name="workflow_definitions",
    )
    op.drop_index(
        "ix_workflow_definitions_project_id",
        table_name="workflow_definitions",
    )
    op.drop_table("workflow_definitions")
