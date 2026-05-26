"""Tests for Redis pub/sub realtime fanout adapter."""

from __future__ import annotations

import asyncio

import pytest

from taskmaster_backend.realtime.redis_fanout import (
    RedisFanoutMessage,
    RedisRealtimeFanoutAdapter,
    deserialize_fanout_message,
    redis_recipient_channel,
    serialize_fanout_message,
)


class RecordingRedisClient:
    def __init__(self) -> None:
        self.published: list[tuple[str, str]] = []

    async def publish(self, channel: str, message: str) -> int:
        self.published.append((channel, message))
        return 1


def test_redis_recipient_channel_is_scoped_to_recipient() -> None:
    assert (
        redis_recipient_channel("taskmaster:realtime", "user-1")
        == "taskmaster:realtime:recipient:user-1"
    )


def test_redis_fanout_serializes_and_deserializes_message_contract() -> None:
    message = RedisFanoutMessage(
        recipient_id="user-1",
        event_type="notification.created",
        payload={"notification_id": "notification-1"},
    )

    serialized = serialize_fanout_message(message)
    deserialized = deserialize_fanout_message(serialized)

    assert deserialized == message


def test_redis_fanout_adapter_publishes_notification_to_recipient_channel() -> None:
    redis_client = RecordingRedisClient()
    adapter = RedisRealtimeFanoutAdapter(
        redis_client,
        channel_prefix="taskmaster:realtime",
    )

    subscriber_count = asyncio.run(
        adapter.publish_notification(
            recipient_id="user-1",
            message={"type": "notification.created"},
        )
    )

    assert subscriber_count == 1
    assert len(redis_client.published) == 1
    channel, raw_message = redis_client.published[0]
    assert channel == "taskmaster:realtime:recipient:user-1"
    message = deserialize_fanout_message(raw_message)
    assert message.recipient_id == "user-1"
    assert message.event_type == "notification.created"
    assert message.payload == {"type": "notification.created"}


def test_redis_fanout_adapter_rejects_empty_scope_values() -> None:
    redis_client = RecordingRedisClient()

    with pytest.raises(ValueError, match="channel_prefix is required"):
        RedisRealtimeFanoutAdapter(redis_client, channel_prefix=" ")

    adapter = RedisRealtimeFanoutAdapter(
        redis_client,
        channel_prefix="taskmaster:realtime",
    )
    with pytest.raises(ValueError, match="recipient_id is required"):
        asyncio.run(adapter.publish_notification(recipient_id=" ", message={}))


def test_deserialize_fanout_message_rejects_invalid_payloads() -> None:
    with pytest.raises(ValueError, match="recipient_id is required"):
        deserialize_fanout_message('{"event_type":"notification.created","payload":{}}')
    with pytest.raises(ValueError, match="event_type is required"):
        deserialize_fanout_message('{"recipient_id":"user-1","payload":{}}')
    with pytest.raises(ValueError, match="payload must be an object"):
        deserialize_fanout_message(
            '{"recipient_id":"user-1","event_type":"notification.created","payload":[]}'
        )


def test_redis_fanout_adapter_does_not_add_subscription_manager_or_network_client() -> None:
    redis_client = RecordingRedisClient()
    adapter = RedisRealtimeFanoutAdapter(
        redis_client,
        channel_prefix="taskmaster:realtime",
    )

    assert not hasattr(adapter, "subscribe")
    assert not hasattr(adapter, "run")
    assert not hasattr(adapter, "connect")
