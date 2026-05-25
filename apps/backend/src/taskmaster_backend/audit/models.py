"""SQLAlchemy models for the Audit domain."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from taskmaster_backend.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(Base):
    """Immutable audit record for security-sensitive actions."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_actor_id_created_at", "actor_id", "created_at"),
        Index(
            "ix_audit_logs_entity_type_entity_id_created_at",
            "entity_type",
            "entity_id",
            "created_at",
        ),
        Index("ix_audit_logs_action_created_at", "action", "created_at"),
        Index("ix_audit_logs_organization_id_created_at", "organization_id", "created_at"),
        Index("ix_audit_logs_workspace_id_created_at", "workspace_id", "created_at"),
        Index("ix_audit_logs_project_id_created_at", "project_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    actor_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    actor_type: Mapped[str] = mapped_column(String(64), nullable=False)
    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workspaces.id"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("projects.id"),
        nullable=True,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    before_summary: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    after_summary: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    diff_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )


class EntityVersion(Base):
    """Immutable snapshot of entity state at a point in time."""

    __tablename__ = "entity_versions"
    __table_args__ = (
        Index(
            "ix_entity_versions_entity_type_entity_id_version",
            "entity_type",
            "entity_id",
            "version_number",
        ),
        Index(
            "ix_entity_versions_entity_type_entity_id_created_at",
            "entity_type",
            "entity_id",
            "created_at",
        ),
        Index("ix_entity_versions_organization_id_created_at", "organization_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    audit_log_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("audit_logs.id"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    entity_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
