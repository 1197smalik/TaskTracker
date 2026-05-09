"""Create workspaces table."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0004_create_workspaces_table"
down_revision = "0003_create_organizations_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_workspaces_organization_id",
        "workspaces",
        ["organization_id"],
        unique=False,
    )
    op.create_index("ix_workspaces_name", "workspaces", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_workspaces_name", table_name="workspaces")
    op.drop_index("ix_workspaces_organization_id", table_name="workspaces")
    op.drop_table("workspaces")
