"""Activity writer service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from taskmaster_backend.activity.models import ActivityEvent
from taskmaster_backend.activity.repository import create_activity_event


@dataclass(frozen=True, slots=True)
class ActivityEventWriteRequest:
    """Request to append a user-facing activity event."""

    entity_type: str
    entity_id: str
    event_type: str
    actor_id: str | None = None
    project_id: str | None = None
    summary: str | None = None
    payload: dict[str, object] = field(default_factory=dict)
    created_at: datetime | None = None


def write_activity_event(
    session: Session,
    request: ActivityEventWriteRequest,
    *,
    commit: bool = True,
) -> ActivityEvent:
    """Append an activity event without dispatching external side effects."""
    _require_non_empty(request.entity_type, "entity_type")
    _require_non_empty(request.entity_id, "entity_id")
    _require_non_empty(request.event_type, "event_type")
    _require_optional_non_empty(request.actor_id, "actor_id")
    _require_optional_non_empty(request.project_id, "project_id")
    _require_optional_non_empty(request.summary, "summary")

    activity_event = ActivityEvent(
        actor_id=request.actor_id,
        project_id=request.project_id,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        event_type=request.event_type,
        summary=request.summary,
        payload=dict(request.payload),
    )
    if request.created_at is not None:
        activity_event.created_at = request.created_at

    return create_activity_event(session, activity_event, commit=commit)


def _require_non_empty(value: str, field_name: str) -> None:
    if value.strip() == "":
        raise ValueError(f"{field_name} is required")


def _require_optional_non_empty(value: str | None, field_name: str) -> None:
    if value is not None and value.strip() == "":
        raise ValueError(f"{field_name} cannot be empty")
