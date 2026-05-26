"""WebSocket authentication helpers."""

from __future__ import annotations

from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal
from taskmaster_backend.identity.tokens import InvalidTokenError, decode_access_token
from taskmaster_backend.realtime.auth_contract import WebSocketCredential


def authenticate_websocket_credential(
    credential: WebSocketCredential,
) -> AuthenticatedPrincipal | None:
    """Validate a WebSocket bearer credential using the existing JWT utility."""
    try:
        claims = decode_access_token(credential.token)
    except InvalidTokenError:
        return None

    return AuthenticatedPrincipal(
        subject=claims.sub,
        issuer=claims.iss,
        audience=claims.aud,
        expires_at=claims.exp,
    )
