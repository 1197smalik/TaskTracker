"""WebSocket authentication handshake contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

WS_ACCEPTED_AUTH_SUBPROTOCOL: Final = "taskmaster.auth"
WS_BEARER_SUBPROTOCOL_PREFIX: Final = "bearer."
WS_MISSING_CREDENTIAL_CLOSE_CODE: Final = 4401
WS_INVALID_CREDENTIAL_CLOSE_CODE: Final = 4403


@dataclass(frozen=True, slots=True)
class WebSocketCredential:
    """Extracted bearer credential from the WebSocket subprotocol list."""

    token: str
    accepted_subprotocol: str = WS_ACCEPTED_AUTH_SUBPROTOCOL


def extract_websocket_bearer_token(subprotocols: list[str]) -> WebSocketCredential | None:
    """Extract bearer token from supported WebSocket subprotocols.

    Browser clients send both `taskmaster.auth` and `bearer.<token>`. The server
    validates the token later and accepts only `taskmaster.auth`, never echoing
    the raw bearer token as the selected subprotocol.
    """
    if WS_ACCEPTED_AUTH_SUBPROTOCOL not in subprotocols:
        return None

    for subprotocol in subprotocols:
        if not subprotocol.startswith(WS_BEARER_SUBPROTOCOL_PREFIX):
            continue
        token = subprotocol.removeprefix(WS_BEARER_SUBPROTOCOL_PREFIX).strip()
        if token == "":
            return None
        return WebSocketCredential(token=token)

    return None


def websocket_auth_uses_query_token() -> bool:
    """Document that query-string token transport is not accepted."""
    return False


def websocket_authorization_boundary() -> str:
    """Document the boundary between handshake auth and subscription auth."""
    return "authenticate_at_handshake_authorize_at_subscription"
