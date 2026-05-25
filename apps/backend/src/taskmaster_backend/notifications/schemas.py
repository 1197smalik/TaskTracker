"""API schemas for notification endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from taskmaster_backend.collaboration.models import Notification


class NotificationApiErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict[str, str] = Field(default_factory=dict)
    correlation_id: str
    field_errors: dict[str, list[str]] = Field(default_factory=dict)
    retry_after: int | None = None


class NotificationResponse(BaseModel):
    id: str
    recipient_id: str
    notification_type: str
    title: str
    body: str | None
    entity_type: str | None
    entity_id: str | None
    payload: dict[str, object]
    read_at: datetime | None
    is_read: bool
    created_at: datetime

    @classmethod
    def from_model(cls, notification: Notification) -> "NotificationResponse":
        return cls(
            id=notification.id,
            recipient_id=notification.recipient_id,
            notification_type=notification.notification_type,
            title=notification.title,
            body=notification.body,
            entity_type=notification.entity_type,
            entity_id=notification.entity_id,
            payload=notification.payload,
            read_at=notification.read_at,
            is_read=notification.read_at is not None,
            created_at=notification.created_at,
        )


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    limit: int
    offset: int
