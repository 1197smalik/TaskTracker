"""Redis pub/sub fanout adapter contract for realtime messages."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol


class RedisPublishClient(Protocol):
    """Minimal async Redis publish contract used by the fanout adapter."""

    async def publish(self, channel: str, message: str) -> int:
        """Publish a serialized message to one Redis channel."""


@dataclass(frozen=True, slots=True)
class RedisFanoutMessage:
    """Serialized realtime fanout message."""

    recipient_id: str
    event_type: str
    payload: dict[str, object]


class RedisRealtimeFanoutAdapter:
    """Publish recipient-scoped realtime messages to Redis pub/sub."""

    def __init__(self, redis_client: RedisPublishClient, *, channel_prefix: str) -> None:
        _require_non_empty(channel_prefix, "channel_prefix")
        self._redis_client = redis_client
        self._channel_prefix = channel_prefix.rstrip(":")

    async def publish_notification(
        self,
        *,
        recipient_id: str,
        message: dict[str, object],
    ) -> int:
        _require_non_empty(recipient_id, "recipient_id")
        fanout_message = RedisFanoutMessage(
            recipient_id=recipient_id,
            event_type="notification.created",
            payload=message,
        )
        return await self._redis_client.publish(
            redis_recipient_channel(self._channel_prefix, recipient_id),
            serialize_fanout_message(fanout_message),
        )


def redis_recipient_channel(channel_prefix: str, recipient_id: str) -> str:
    """Build the recipient-scoped realtime Redis channel name."""
    _require_non_empty(channel_prefix, "channel_prefix")
    _require_non_empty(recipient_id, "recipient_id")
    return f"{channel_prefix.rstrip(':')}:recipient:{recipient_id}"


def serialize_fanout_message(message: RedisFanoutMessage) -> str:
    """Serialize a fanout message deterministically for Redis pub/sub."""
    return json.dumps(
        {
            "recipient_id": message.recipient_id,
            "event_type": message.event_type,
            "payload": message.payload,
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def deserialize_fanout_message(raw_message: str) -> RedisFanoutMessage:
    """Deserialize a Redis fanout message into a typed contract."""
    decoded = json.loads(raw_message)
    if not isinstance(decoded, dict):
        raise ValueError("fanout message must be a JSON object")

    recipient_id = decoded.get("recipient_id")
    event_type = decoded.get("event_type")
    payload = decoded.get("payload")
    if not isinstance(recipient_id, str) or recipient_id.strip() == "":
        raise ValueError("recipient_id is required")
    if not isinstance(event_type, str) or event_type.strip() == "":
        raise ValueError("event_type is required")
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")

    return RedisFanoutMessage(
        recipient_id=recipient_id,
        event_type=event_type,
        payload=dict(payload),
    )


def _require_non_empty(value: str, field_name: str) -> None:
    if value.strip() == "":
        raise ValueError(f"{field_name} is required")
