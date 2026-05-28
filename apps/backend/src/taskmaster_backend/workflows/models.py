"""SQLAlchemy models for the Workflow Engine domain."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
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
        CheckConstraint(
            "position >= 0",
            name="ck_workflow_states_position_non_negative",
        ),
        Index(
            "ix_workflow_states_workflow_definition_id_name",
            "workflow_definition_id",
            "name",
        ),
        Index(
            "ix_workflow_states_workflow_definition_id_position",
            "workflow_definition_id",
            "position",
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
    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
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


class WorkflowTransition(Base):
    """Directed movement between two states in a workflow definition."""

    __tablename__ = "workflow_transitions"
    __table_args__ = (
        UniqueConstraint(
            "workflow_definition_id",
            "source_state_id",
            "target_state_id",
            name="uq_workflow_transitions_workflow_definition_id_source_target",
        ),
        CheckConstraint(
            "source_state_id != target_state_id",
            name="ck_workflow_transitions_distinct_states",
        ),
        Index(
            "ix_workflow_transitions_workflow_definition_id_source_state_id",
            "workflow_definition_id",
            "source_state_id",
        ),
        Index(
            "ix_workflow_transitions_workflow_definition_id_target_state_id",
            "workflow_definition_id",
            "target_state_id",
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
    source_state_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workflow_states.id"),
        nullable=False,
    )
    target_state_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workflow_states.id"),
        nullable=False,
    )
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


class WorkflowTransitionRule(Base):
    """Structured rule metadata attached to a workflow transition."""

    __tablename__ = "workflow_transition_rules"
    __table_args__ = (
        UniqueConstraint(
            "workflow_transition_id",
            "rule_type",
            name="uq_workflow_transition_rules_transition_id_rule_type",
        ),
        CheckConstraint(
            "rule_type IN ("
            "'required_fields', "
            "'allowed_roles', "
            "'assignee_reporter', "
            "'parent_child_completion', "
            "'comment_required'"
            ")",
            name="ck_workflow_transition_rules_type_supported",
        ),
        Index(
            "ix_workflow_transition_rules_transition_id_rule_type",
            "workflow_transition_id",
            "rule_type",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    workflow_transition_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workflow_transitions.id"),
        nullable=False,
        index=True,
    )
    rule_type: Mapped[str] = mapped_column(String(64), nullable=False)
    config: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
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


class WorkflowAssignment(Base):
    """Project assignment to its active workflow definition."""

    __tablename__ = "workflow_assignments"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            name="uq_workflow_assignments_project_id",
        ),
        Index(
            "ix_workflow_assignments_project_id_workflow_definition_id",
            "project_id",
            "workflow_definition_id",
        ),
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
    workflow_definition_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workflow_definitions.id"),
        nullable=False,
        index=True,
    )
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
