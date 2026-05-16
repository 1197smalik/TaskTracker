"""SQLAlchemy models for the Workflow Engine domain."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from taskmaster_backend.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkflowDefinition(Base):
    """Named project-scoped workflow lifecycle definition."""

    __tablename__ = "workflow_definitions"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "name",
            "version",
            name="uq_workflow_definitions_project_id_name_version",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_workflow_definitions_version_positive",
        ),
        Index("ix_workflow_definitions_project_id_name", "project_id", "name"),
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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
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


class WorkflowState(Base):
    """Lifecycle state contained by a workflow definition."""

    __tablename__ = "workflow_states"
    __table_args__ = (
        UniqueConstraint(
            "workflow_definition_id",
            "name",
            name="uq_workflow_states_workflow_definition_id_name",
        ),
        Index(
            "ix_workflow_states_workflow_definition_id_name",
            "workflow_definition_id",
            "name",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    workflow_definition_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workflow_definitions.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
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
