"""Create audit_logs table."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0013_create_audit_logs_table"
down_revision = "0012_assign_workflows_to_projects"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("actor_id", sa.String(length=36), nullable=True),
        sa.Column("actor_type", sa.String(length=64), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=True),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("before_summary", sa.JSON(), nullable=True),
        sa.Column("after_summary", sa.JSON(), nullable=True),
        sa.Column("diff_reference", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"], unique=False)
    op.create_index(
        "ix_audit_logs_actor_id_created_at",
        "audit_logs",
        ["actor_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_entity_type_entity_id_created_at",
        "audit_logs",
        ["entity_type", "entity_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_action_created_at",
        "audit_logs",
        ["action", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_organization_id",
        "audit_logs",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_organization_id_created_at",
        "audit_logs",
        ["organization_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_workspace_id",
        "audit_logs",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_workspace_id_created_at",
        "audit_logs",
        ["workspace_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_project_id",
        "audit_logs",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_project_id_created_at",
        "audit_logs",
        ["project_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_project_id_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_project_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_workspace_id_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_workspace_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_organization_id_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_organization_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action_created_at", table_name="audit_logs")
    op.drop_index(
        "ix_audit_logs_entity_type_entity_id_created_at",
        table_name="audit_logs",
    )
    op.drop_index("ix_audit_logs_actor_id_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_table("audit_logs")
