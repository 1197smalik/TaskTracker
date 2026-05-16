"""Create projects table."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0007_create_projects_table"
down_revision = "0006_create_permissions_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("key", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "key",
            name="uq_projects_workspace_id_key",
        ),
    )
    op.create_index("ix_projects_workspace_id", "projects", ["workspace_id"], unique=False)
    op.create_index(
        "ix_projects_workspace_id_key",
        "projects",
        ["workspace_id", "key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_projects_workspace_id_key", table_name="projects")
    op.drop_index("ix_projects_workspace_id", table_name="projects")
    op.drop_table("projects")
