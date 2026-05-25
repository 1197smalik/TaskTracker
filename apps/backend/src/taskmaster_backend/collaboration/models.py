"""SQLAlchemy models for the Collaboration domain."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from taskmaster_backend.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Comment(Base):
    """User-authored comment attached to a work item."""

    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint("length(body) > 0", name="ck_comments_body_non_empty"),
        Index("ix_comments_work_item_id_created_at", "work_item_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    work_item_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("work_items.id"),
        nullable=False,
    )
    author_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
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
