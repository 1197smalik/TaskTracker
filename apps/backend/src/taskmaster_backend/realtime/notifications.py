"""In-process WebSocket notification dispatcher."""

from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from taskmaster_backend.collaboration.models import Notification


class RealtimeNotificationConnection(Protocol):
    """Minimal WebSocket connection contract used by the dispatcher."""

    async def send_json(self, data: dict[str, object]) -> None:
        """Send one JSON-serializable realtime notification payload."""


class WebSocketNotificationDispatcher:
    """Best-effort in-process dispatcher for recipient-scoped notifications."""

    def __init__(self) -> None:
        self._connections_by_recipient: dict[
            str,
            list[RealtimeNotificationConnection],
        ] = defaultdict(list)

    def register(
        self,
        *,
        recipient_id: str,
        connection: RealtimeNotificationConnection,
    ) -> None:
        _require_non_empty(recipient_id, "recipient_id")
        connections = self._connections_by_recipient[recipient_id]
        if connection not in connections:
            connections.append(connection)

    def unregister(
        self,
        *,
        recipient_id: str,
        connection: RealtimeNotificationConnection,
    ) -> None:
        connections = self._connections_by_recipient.get(recipient_id)
        if connections is None:
            return
        if connection in connections:
            connections.remove(connection)
        if not connections:
            del self._connections_by_recipient[recipient_id]

    async def dispatch_notification_created(
        self,
        notification: Notification,
    ) -> int:
        """Dispatch a notification-created event to recipient-owned connections."""
        connections = list(self._connections_by_recipient.get(notification.recipient_id, ()))
        delivered_count = 0
        for connection in connections:
            await connection.send_json(build_notification_created_message(notification))
            delivered_count += 1
        return delivered_count


def build_notification_created_message(
    notification: Notification,
) -> dict[str, object]:
    """Build the stable realtime notification payload."""
    return {
        "type": "notification.created",
        "notification": {
            "id": notification.id,
            "recipient_id": notification.recipient_id,
            "organization_id": notification.organization_id,
            "workspace_id": notification.workspace_id,
            "project_id": notification.project_id,
            "notification_type": notification.notification_type,
            "title": notification.title,
            "body": notification.body,
            "entity_type": notification.entity_type,
            "entity_id": notification.entity_id,
            "payload": dict(notification.payload),
            "read_at": notification.read_at.isoformat() if notification.read_at else None,
            "created_at": notification.created_at.isoformat(),
        },
    }


def _require_non_empty(value: str, field_name: str) -> None:
    if value.strip() == "":
        raise ValueError(f"{field_name} is required")
