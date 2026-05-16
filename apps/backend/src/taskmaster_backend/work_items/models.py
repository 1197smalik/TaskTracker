"""SQLAlchemy models for the Work Item domain."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from taskmaster_backend.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkItem(Base):
    """Generic project-scoped work item model."""

    __tablename__ = "work_items"
    __table_args__ = (
        CheckConstraint(
            "type IN ('task', 'bug', 'story', 'incident', 'subtask')",
            name="ck_work_items_type_supported",
        ),
        CheckConstraint("version >= 1", name="ck_work_items_version_positive"),
        Index("ix_work_items_project_id_id", "project_id", "id"),
        Index("ix_work_items_project_id_current_state_id", "project_id", "current_state_id"),
        Index("ix_work_items_project_id_assignee_id_status", "project_id", "assignee_id", "status"),
        Index("ix_work_items_project_id_type_priority", "project_id", "type", "priority"),
        Index("ix_work_items_project_id_sprint_id", "project_id", "sprint_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    sprint_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("sprints.id"),
        nullable=True,
    )
    epic_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("epics.id"),
        nullable=True,
    )
    assignee_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=True,
    )
    reporter_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=True,
    )
    current_state_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str | None] = mapped_column(String(64), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(64), nullable=True)
    estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    typed_metadata: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
