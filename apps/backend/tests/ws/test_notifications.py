"""Tests for websocket notification dispatcher."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from taskmaster_backend.collaboration.models import Notification
from taskmaster_backend.realtime.notifications import (
    WebSocketNotificationDispatcher,
    build_notification_created_message,
)


class RecordingConnection:
    def __init__(self) -> None:
        self.messages: list[dict[str, object]] = []

    async def send_json(self, data: dict[str, object]) -> None:
        self.messages.append(data)


def _notification(*, recipient_id: str = "user-1") -> Notification:
    return Notification(
        id="notification-1",
        recipient_id=recipient_id,
        organization_id="org-1",
        workspace_id="workspace-1",
        project_id="project-1",
        notification_type="comment.mention",
        title="You were mentioned",
        body=None,
        entity_type="comment",
        entity_id="comment-1",
        payload={"source_event_id": "event-1"},
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_build_notification_created_message_has_stable_shape() -> None:
    message = build_notification_created_message(_notification())

    assert message["type"] == "notification.created"
    notification_payload = message["notification"]
    assert isinstance(notification_payload, dict)
    assert notification_payload["id"] == "notification-1"
    assert notification_payload["recipient_id"] == "user-1"
    assert notification_payload["notification_type"] == "comment.mention"
    assert notification_payload["payload"] == {"source_event_id": "event-1"}
    assert notification_payload["read_at"] is None
    assert notification_payload["created_at"] == "2026-01-01T00:00:00+00:00"


def test_dispatcher_sends_notification_to_matching_recipient_connections() -> None:
    dispatcher = WebSocketNotificationDispatcher()
    connection = RecordingConnection()
    dispatcher.register(recipient_id="user-1", connection=connection)

    delivered_count = asyncio.run(
        dispatcher.dispatch_notification_created(_notification(recipient_id="user-1"))
    )

    assert delivered_count == 1
    assert len(connection.messages) == 1
    assert connection.messages[0]["type"] == "notification.created"


def test_dispatcher_does_not_send_notification_to_other_recipients() -> None:
    dispatcher = WebSocketNotificationDispatcher()
    matching_connection = RecordingConnection()
    other_connection = RecordingConnection()
    dispatcher.register(recipient_id="user-1", connection=matching_connection)
    dispatcher.register(recipient_id="user-2", connection=other_connection)

    delivered_count = asyncio.run(
        dispatcher.dispatch_notification_created(_notification(recipient_id="user-1"))
    )

    assert delivered_count == 1
    assert len(matching_connection.messages) == 1
    assert other_connection.messages == []


def test_dispatcher_unregister_removes_connection() -> None:
    dispatcher = WebSocketNotificationDispatcher()
    connection = RecordingConnection()
    dispatcher.register(recipient_id="user-1", connection=connection)
    dispatcher.unregister(recipient_id="user-1", connection=connection)

    delivered_count = asyncio.run(
        dispatcher.dispatch_notification_created(_notification(recipient_id="user-1"))
    )

    assert delivered_count == 0
    assert connection.messages == []


def test_dispatcher_avoids_duplicate_connection_registration() -> None:
    dispatcher = WebSocketNotificationDispatcher()
    connection = RecordingConnection()
    dispatcher.register(recipient_id="user-1", connection=connection)
    dispatcher.register(recipient_id="user-1", connection=connection)

    delivered_count = asyncio.run(
        dispatcher.dispatch_notification_created(_notification(recipient_id="user-1"))
    )

    assert delivered_count == 1
    assert len(connection.messages) == 1


def test_dispatcher_rejects_empty_recipient_registration() -> None:
    dispatcher = WebSocketNotificationDispatcher()

    with pytest.raises(ValueError, match="recipient_id is required"):
        dispatcher.register(recipient_id=" ", connection=RecordingConnection())


def test_dispatcher_does_not_expose_future_fanout_or_subscription_state() -> None:
    dispatcher = WebSocketNotificationDispatcher()

    assert not hasattr(dispatcher, "redis")
    assert not hasattr(dispatcher, "pubsub")
    assert not hasattr(dispatcher, "join_project")
    assert not hasattr(dispatcher, "subscribe")
