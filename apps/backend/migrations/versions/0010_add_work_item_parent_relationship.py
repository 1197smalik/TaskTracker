"""Add work item parent relationship."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0010_add_work_item_parent_relationship"
down_revision = "0009_create_work_items_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column("work_items", sa.Column("parent_id", sa.String(length=36), nullable=True))
    if bind.dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_work_items_parent_id_work_items",
            "work_items",
            "work_items",
            ["parent_id"],
            ["id"],
        )
        op.create_check_constraint(
            "ck_work_items_not_self_parent",
            "work_items",
            "parent_id IS NULL OR parent_id != id",
        )

    op.create_index(
        "ix_work_items_project_id_parent_id",
        "work_items",
        ["project_id", "parent_id"],
        unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_work_items_project_id_parent_id", table_name="work_items")

    if bind.dialect.name != "sqlite":
        op.drop_constraint("ck_work_items_not_self_parent", "work_items", type_="check")
        op.drop_constraint(
            "fk_work_items_parent_id_work_items",
            "work_items",
            type_="foreignkey",
        )
    op.drop_column("work_items", "parent_id")
