"""Create roles table."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0005_create_roles_table"
down_revision = "0004_create_workspaces_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("scope", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "scope", name="uq_roles_name_scope"),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=False)
    op.create_index("ix_roles_scope", "roles", ["scope"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_roles_scope", table_name="roles")
    op.drop_index("ix_roles_name", table_name="roles")
    op.drop_table("roles")
