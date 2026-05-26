"""Realtime/WebSocket domain contracts."""

from taskmaster_backend.realtime.auth import authenticate_websocket_credential
from taskmaster_backend.realtime.auth_contract import (
    WS_ACCEPTED_AUTH_SUBPROTOCOL,
    WS_BEARER_SUBPROTOCOL_PREFIX,
    WS_INVALID_CREDENTIAL_CLOSE_CODE,
    WS_MISSING_CREDENTIAL_CLOSE_CODE,
    WebSocketCredential,
    extract_websocket_bearer_token,
    websocket_auth_uses_query_token,
    websocket_authorization_boundary,
)
from taskmaster_backend.realtime.notifications import (
    RealtimeNotificationConnection,
    WebSocketNotificationDispatcher,
    build_notification_created_message,
)
from taskmaster_backend.realtime.redis_fanout import (
    RedisFanoutMessage,
    RedisPublishClient,
    RedisRealtimeFanoutAdapter,
    deserialize_fanout_message,
    redis_recipient_channel,
    serialize_fanout_message,
)

__all__ = [
    "WS_ACCEPTED_AUTH_SUBPROTOCOL",
    "WS_BEARER_SUBPROTOCOL_PREFIX",
    "WS_INVALID_CREDENTIAL_CLOSE_CODE",
    "WS_MISSING_CREDENTIAL_CLOSE_CODE",
    "WebSocketCredential",
    "RealtimeNotificationConnection",
    "RedisFanoutMessage",
    "RedisPublishClient",
    "RedisRealtimeFanoutAdapter",
    "WebSocketNotificationDispatcher",
    "authenticate_websocket_credential",
    "build_notification_created_message",
    "deserialize_fanout_message",
    "extract_websocket_bearer_token",
    "redis_recipient_channel",
    "serialize_fanout_message",
    "websocket_auth_uses_query_token",
    "websocket_authorization_boundary",
]
