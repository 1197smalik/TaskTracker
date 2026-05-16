"""Create boards table."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0008_create_boards_table"
down_revision = "0007_create_projects_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "boards",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_boards_project_id", "boards", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_boards_project_id", table_name="boards")
    op.drop_table("boards")
