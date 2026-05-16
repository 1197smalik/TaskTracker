"""Create work_items table."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0009_create_work_items_table"
down_revision = "0008_create_boards_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "work_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("sprint_id", sa.String(length=36), nullable=True),
        sa.Column("epic_id", sa.String(length=36), nullable=True),
        sa.Column("assignee_id", sa.String(length=36), nullable=True),
        sa.Column("reporter_id", sa.String(length=36), nullable=True),
        sa.Column("current_state_id", sa.String(length=36), nullable=True),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=64), nullable=True),
        sa.Column("severity", sa.String(length=64), nullable=True),
        sa.Column("estimate", sa.Integer(), nullable=True),
        sa.Column("typed_metadata", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "type IN ('task', 'bug', 'story', 'incident', 'subtask')",
            name="ck_work_items_type_supported",
        ),
        sa.CheckConstraint("version >= 1", name="ck_work_items_version_positive"),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["epic_id"], ["epics.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["sprint_id"], ["sprints.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_work_items_project_id", "work_items", ["project_id"], unique=False)
    op.create_index(
        "ix_work_items_project_id_assignee_id_status",
        "work_items",
        ["project_id", "assignee_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_work_items_project_id_current_state_id",
        "work_items",
        ["project_id", "current_state_id"],
        unique=False,
    )
    op.create_index(
        "ix_work_items_project_id_id",
        "work_items",
        ["project_id", "id"],
        unique=False,
    )
    op.create_index(
        "ix_work_items_project_id_sprint_id",
        "work_items",
        ["project_id", "sprint_id"],
        unique=False,
    )
    op.create_index(
        "ix_work_items_project_id_type_priority",
        "work_items",
        ["project_id", "type", "priority"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_work_items_project_id_type_priority", table_name="work_items")
    op.drop_index("ix_work_items_project_id_sprint_id", table_name="work_items")
    op.drop_index("ix_work_items_project_id_id", table_name="work_items")
    op.drop_index("ix_work_items_project_id_current_state_id", table_name="work_items")
    op.drop_index(
        "ix_work_items_project_id_assignee_id_status",
        table_name="work_items",
    )
    op.drop_index("ix_work_items_project_id", table_name="work_items")
    op.drop_table("work_items")
