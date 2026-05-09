"""Create organizations table."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0003_create_organizations_table"
down_revision = "0002_create_users_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organizations_name", "organizations", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_organizations_name", table_name="organizations")
    op.drop_table("organizations")
