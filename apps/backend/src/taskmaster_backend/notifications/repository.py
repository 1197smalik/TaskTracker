"""Persistence helpers for notification creation."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from taskmaster_backend.collaboration.models import Notification


def find_notification_by_source_event(
    session: Session,
    *,
    recipient_id: str,
    notification_type: str,
    entity_type: str,
    entity_id: str,
    source_event_id: str,
) -> Notification | None:
    """Find an existing notification for idempotent event processing."""
    candidates = session.scalars(
        select(Notification).where(
            Notification.recipient_id == recipient_id,
            Notification.notification_type == notification_type,
            Notification.entity_type == entity_type,
            Notification.entity_id == entity_id,
        )
    )
    for notification in candidates:
        if notification.payload.get("source_event_id") == source_event_id:
            return notification
    return None


def create_notification(
    session: Session,
    *,
    recipient_id: str,
    organization_id: str,
    workspace_id: str | None,
    project_id: str | None,
    notification_type: str,
    title: str,
    body: str | None,
    entity_type: str,
    entity_id: str,
    payload: dict[str, object],
) -> Notification:
    notification = Notification(
        recipient_id=recipient_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        project_id=project_id,
        notification_type=notification_type,
        title=title,
        body=body,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=payload,
    )
    session.add(notification)
    return notification


def list_notifications_for_recipient(
    session: Session,
    *,
    recipient_id: str,
    limit: int,
    offset: int,
) -> tuple[list[Notification], int]:
    """List notifications scoped to one recipient."""
    total = session.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.recipient_id == recipient_id)
    )
    notifications = list(
        session.scalars(
            select(Notification)
            .where(Notification.recipient_id == recipient_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    return notifications, total or 0


def get_notification_for_recipient(
    session: Session,
    *,
    notification_id: str,
    recipient_id: str,
) -> Notification | None:
    """Return a notification only when it belongs to the recipient."""
    return session.scalars(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_id == recipient_id,
        )
    ).first()
