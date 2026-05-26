"""Tests for WebSocket authentication handshake."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import cast

import jwt
import pytest
from fastapi import WebSocket
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocketDisconnect

from taskmaster_backend.app import create_app
from taskmaster_backend.core import config as config_module
from taskmaster_backend.identity.tokens import create_access_token
from taskmaster_backend.realtime.auth import authenticate_websocket_credential
from taskmaster_backend.realtime.auth_contract import (
    WS_ACCEPTED_AUTH_SUBPROTOCOL,
    WS_INVALID_CREDENTIAL_CLOSE_CODE,
    WS_MISSING_CREDENTIAL_CLOSE_CODE,
    WebSocketCredential,
)
from taskmaster_backend.realtime.routes import websocket_authentication_handshake

TEST_JWT_SECRET = "test-secret-value-with-32-plus-bytes"
WRONG_TEST_JWT_SECRET = "wrong-secret-value-with-32-plus-bytes"


def test_websocket_accepts_valid_subprotocol_bearer_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_test_jwt_settings(monkeypatch, ttl_seconds=900)
    token = create_access_token("user-123")
    websocket = _FakeWebSocket(
        subprotocols=[WS_ACCEPTED_AUTH_SUBPROTOCOL, f"bearer.{token}"]
    )

    asyncio.run(websocket_authentication_handshake(cast(WebSocket, websocket)))

    assert websocket.accepted_subprotocol == WS_ACCEPTED_AUTH_SUBPROTOCOL
    assert websocket.closed_code is None


def test_websocket_rejects_missing_credentials() -> None:
    websocket = _FakeWebSocket(subprotocols=[WS_ACCEPTED_AUTH_SUBPROTOCOL])

    asyncio.run(websocket_authentication_handshake(cast(WebSocket, websocket)))

    assert websocket.accepted_subprotocol is None
    assert websocket.closed_code == WS_MISSING_CREDENTIAL_CLOSE_CODE


def test_websocket_rejects_invalid_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_test_jwt_settings(monkeypatch, ttl_seconds=900)
    invalid_token = jwt.encode(
        {
            "sub": "user-123",
            "exp": datetime.now(UTC) + timedelta(minutes=15),
            "iss": "test-issuer",
            "aud": "test-audience",
        },
        WRONG_TEST_JWT_SECRET,
        algorithm="HS256",
    )
    websocket = _FakeWebSocket(
        subprotocols=[WS_ACCEPTED_AUTH_SUBPROTOCOL, f"bearer.{invalid_token}"]
    )

    asyncio.run(websocket_authentication_handshake(cast(WebSocket, websocket)))

    assert websocket.accepted_subprotocol is None
    assert websocket.closed_code == WS_INVALID_CREDENTIAL_CLOSE_CODE


def test_websocket_does_not_accept_query_string_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_test_jwt_settings(monkeypatch, ttl_seconds=900)
    token = create_access_token("user-123")
    websocket = _FakeWebSocket(subprotocols=[], query_string=f"token={token}")

    asyncio.run(websocket_authentication_handshake(cast(WebSocket, websocket)))

    assert websocket.accepted_subprotocol is None
    assert websocket.closed_code == WS_MISSING_CREDENTIAL_CLOSE_CODE


def test_websocket_route_is_registered_under_versioned_api() -> None:
    app = create_app()
    websocket_routes = [
        route
        for route in app.routes
        if isinstance(route, WebSocketRoute) and route.path == "/api/v1/ws"
    ]

    assert len(websocket_routes) == 1


def test_websocket_authentication_uses_existing_jwt_decoder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_test_jwt_settings(monkeypatch, ttl_seconds=900)
    token = create_access_token("user-123")

    principal = authenticate_websocket_credential(WebSocketCredential(token=token))

    assert principal is not None
    assert principal.subject == "user-123"
    assert principal.issuer == "test-issuer"
    assert principal.audience == "test-audience"


def test_websocket_authentication_rejects_invalid_jwt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_test_jwt_settings(monkeypatch, ttl_seconds=900)

    assert (
        authenticate_websocket_credential(WebSocketCredential(token="not-a-jwt"))
        is None
    )


def _set_test_jwt_settings(monkeypatch: pytest.MonkeyPatch, *, ttl_seconds: int) -> None:
    monkeypatch.setenv("TASKMASTER_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setenv("TASKMASTER_JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("TASKMASTER_JWT_ISSUER", "test-issuer")
    monkeypatch.setenv("TASKMASTER_JWT_AUDIENCE", "test-audience")
    monkeypatch.setenv("TASKMASTER_JWT_ACCESS_TOKEN_TTL_SECONDS", str(ttl_seconds))
    config_module.reset_settings_cache()


class _FakeWebSocket:
    def __init__(self, *, subprotocols: list[str], query_string: str = "") -> None:
        self.scope: dict[str, object] = {
            "subprotocols": subprotocols,
            "query_string": query_string.encode("utf-8"),
        }
        self.accepted_subprotocol: str | None = None
        self.closed_code: int | None = None

    async def close(self, code: int = 1000, reason: str | None = None) -> None:
        self.closed_code = code

    async def accept(
        self,
        subprotocol: str | None = None,
        headers: list[tuple[bytes, bytes]] | None = None,
    ) -> None:
        self.accepted_subprotocol = subprotocol

    async def receive_text(self) -> str:
        raise WebSocketDisconnect(code=1000)
