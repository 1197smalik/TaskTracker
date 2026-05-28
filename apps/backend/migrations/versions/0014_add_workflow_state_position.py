"""Add workflow state position."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0014_add_workflow_state_position"
down_revision = "0013_create_audit_logs_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("workflow_states") as batch_op:
        batch_op.add_column(
            sa.Column(
                "position",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.create_check_constraint(
            "ck_workflow_states_position_non_negative",
            "position >= 0",
        )
        batch_op.create_index(
            "ix_workflow_states_workflow_definition_id_position",
            ["workflow_definition_id", "position"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("workflow_states") as batch_op:
        batch_op.drop_index("ix_workflow_states_workflow_definition_id_position")
        batch_op.drop_constraint("ck_workflow_states_position_non_negative", type_="check")
        batch_op.drop_column("position")
