"""Assign workflows to projects."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0012_assign_workflows_to_projects"
down_revision = "0011_create_workflow_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_assignments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("workflow_definition_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(
            ["workflow_definition_id"],
            ["workflow_definitions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            name="uq_workflow_assignments_project_id",
        ),
    )
    op.create_index(
        "ix_workflow_assignments_project_id",
        "workflow_assignments",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_workflow_assignments_workflow_definition_id",
        "workflow_assignments",
        ["workflow_definition_id"],
        unique=False,
    )
    op.create_index(
        "ix_workflow_assignments_project_id_workflow_definition_id",
        "workflow_assignments",
        ["project_id", "workflow_definition_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workflow_assignments_project_id_workflow_definition_id",
        table_name="workflow_assignments",
    )
    op.drop_index(
        "ix_workflow_assignments_workflow_definition_id",
        table_name="workflow_assignments",
    )
    op.drop_index(
        "ix_workflow_assignments_project_id",
        table_name="workflow_assignments",
    )
    op.drop_table("workflow_assignments")
