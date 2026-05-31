"""Add minimal organization ownership link and backfill legacy organizations."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0015_add_organization_owner_user_id"
down_revision = "0014_add_workflow_state_position"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    with op.batch_alter_table("organizations") as batch_op:
        batch_op.add_column(
            sa.Column("owner_user_id", sa.String(length=36), nullable=True)
        )
        batch_op.create_index(
            "ix_organizations_owner_user_id",
            ["owner_user_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_organizations_owner_user_id_users",
            "users",
            ["owner_user_id"],
            ["id"],
        )

    owner_user_id = bind.execute(
        sa.text(
            "SELECT id FROM users "
            "WHERE is_active = true "
            "ORDER BY created_at ASC, id ASC "
            "LIMIT 1"
        )
    ).scalar()
    if owner_user_id is not None:
        bind.execute(
            sa.text(
                "UPDATE organizations "
                "SET owner_user_id = :owner_user_id "
                "WHERE owner_user_id IS NULL"
            ),
            {"owner_user_id": owner_user_id},
        )


def downgrade() -> None:
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.drop_constraint(
            "fk_organizations_owner_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_organizations_owner_user_id")
        batch_op.drop_column("owner_user_id")
