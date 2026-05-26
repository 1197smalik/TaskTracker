"""Realtime/WebSocket domain contracts."""

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

__all__ = [
    "WS_ACCEPTED_AUTH_SUBPROTOCOL",
    "WS_BEARER_SUBPROTOCOL_PREFIX",
    "WS_INVALID_CREDENTIAL_CLOSE_CODE",
    "WS_MISSING_CREDENTIAL_CLOSE_CODE",
    "WebSocketCredential",
    "extract_websocket_bearer_token",
    "websocket_auth_uses_query_token",
    "websocket_authorization_boundary",
]
