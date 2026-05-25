"""Persistence helpers for activity events."""

from __future__ import annotations

from sqlalchemy.orm import Session

from taskmaster_backend.activity.models import ActivityEvent


def create_activity_event(
    session: Session,
    activity_event: ActivityEvent,
    *,
    commit: bool = True,
) -> ActivityEvent:
    session.add(activity_event)
    session.flush()

    if commit:
        session.commit()
        session.refresh(activity_event)

    return activity_event
