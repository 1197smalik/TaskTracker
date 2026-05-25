"""Notification creation service for internal source events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from taskmaster_backend.audit.models import EventOutbox
from taskmaster_backend.collaboration.events import COMMENT_MENTION_DETECTED_EVENT_TYPE
from taskmaster_backend.collaboration.models import Notification
from taskmaster_backend.notifications.repository import (
    create_notification,
    find_notification_by_source_event,
    get_notification_for_recipient,
    list_notifications_for_recipient,
)

MENTION_NOTIFICATION_TYPE = "comment.mention"
MENTION_NOTIFICATION_TITLE = "You were mentioned in a comment"


@dataclass(frozen=True, slots=True)
class NotificationCreationResult:
    """Outcome from processing one notification source event."""

    created_count: int
    skipped_count: int
    reason: str | None = None


def list_recipient_notifications(
    session: Session,
    *,
    recipient_id: str,
    limit: int,
    offset: int,
) -> tuple[list[Notification], int]:
    """List notifications for one authenticated recipient."""
    return list_notifications_for_recipient(
        session,
        recipient_id=recipient_id,
        limit=limit,
        offset=offset,
    )


def mark_recipient_notification_read(
    session: Session,
    *,
    recipient_id: str,
    notification_id: str,
) -> Notification | None:
    """Mark one recipient-owned notification as read."""
    notification = get_notification_for_recipient(
        session,
        notification_id=notification_id,
        recipient_id=recipient_id,
    )
    if notification is None:
        return None
    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(notification)
    return notification


def create_notifications_from_event(
    session: Session,
    event: EventOutbox,
) -> NotificationCreationResult:
    """Create notification rows from supported internal source events."""
    if event.event_type != COMMENT_MENTION_DETECTED_EVENT_TYPE:
        return NotificationCreationResult(
            created_count=0,
            skipped_count=0,
            reason="unsupported_event_type",
        )

    resolved_user_ids = _resolved_user_ids(event.payload)
    if not resolved_user_ids:
        return NotificationCreationResult(
            created_count=0,
            skipped_count=0,
            reason="no_resolved_recipients",
        )

    created_count = 0
    skipped_count = 0
    for recipient_id in resolved_user_ids:
        existing = find_notification_by_source_event(
            session,
            recipient_id=recipient_id,
            notification_type=MENTION_NOTIFICATION_TYPE,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            source_event_id=event.event_id,
        )
        if existing is not None:
            skipped_count += 1
            continue

        create_notification(
            session,
            recipient_id=recipient_id,
            organization_id=event.organization_id,
            workspace_id=event.workspace_id,
            project_id=event.project_id,
            notification_type=MENTION_NOTIFICATION_TYPE,
            title=MENTION_NOTIFICATION_TITLE,
            body=None,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            payload=_notification_payload(event),
        )
        session.flush()
        created_count += 1

    return NotificationCreationResult(
        created_count=created_count,
        skipped_count=skipped_count,
        reason=None,
    )


def _resolved_user_ids(payload: dict[str, object]) -> list[str]:
    resolution = payload.get("mention_recipient_resolution")
    if not isinstance(resolution, dict):
        return []
    raw_resolved_user_ids = resolution.get("resolved_user_ids")
    if not isinstance(raw_resolved_user_ids, list):
        return []

    resolved_user_ids: list[str] = []
    seen: set[str] = set()
    for value in raw_resolved_user_ids:
        if not isinstance(value, str):
            continue
        recipient_id = value.strip()
        if recipient_id == "" or recipient_id in seen:
            continue
        resolved_user_ids.append(recipient_id)
        seen.add(recipient_id)
    return resolved_user_ids


def _notification_payload(event: EventOutbox) -> dict[str, object]:
    payload = dict(event.payload)
    payload["source_event_id"] = event.event_id
    payload["source_event_type"] = event.event_type
    return payload
