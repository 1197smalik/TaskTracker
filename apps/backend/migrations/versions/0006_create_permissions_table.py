"""Create permissions table."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0006_create_permissions_table"
down_revision = "0005_create_roles_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_permissions_code", table_name="permissions")
    op.drop_table("permissions")
