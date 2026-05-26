"""Tests for WebSocket authentication handshake contract."""

from __future__ import annotations

from fastapi.routing import APIRoute

from taskmaster_backend.app import create_app
from taskmaster_backend.realtime.auth_contract import (
    WS_ACCEPTED_AUTH_SUBPROTOCOL,
    WS_BEARER_SUBPROTOCOL_PREFIX,
    WS_INVALID_CREDENTIAL_CLOSE_CODE,
    WS_MISSING_CREDENTIAL_CLOSE_CODE,
    extract_websocket_bearer_token,
    websocket_auth_uses_query_token,
    websocket_authorization_boundary,
)


def test_websocket_auth_transport_contract_uses_subprotocol_bearer_token() -> None:
    credential = extract_websocket_bearer_token(
        [WS_ACCEPTED_AUTH_SUBPROTOCOL, f"{WS_BEARER_SUBPROTOCOL_PREFIX}jwt-token"]
    )

    assert credential is not None
    assert credential.token == "jwt-token"
    assert credential.accepted_subprotocol == WS_ACCEPTED_AUTH_SUBPROTOCOL


def test_websocket_auth_contract_does_not_echo_raw_bearer_subprotocol() -> None:
    credential = extract_websocket_bearer_token(
        [WS_ACCEPTED_AUTH_SUBPROTOCOL, "bearer.jwt-token"]
    )

    assert credential is not None
    assert credential.accepted_subprotocol == "taskmaster.auth"
    assert credential.accepted_subprotocol != "bearer.jwt-token"


def test_websocket_auth_contract_rejects_missing_or_empty_credentials() -> None:
    assert extract_websocket_bearer_token([]) is None
    assert extract_websocket_bearer_token(["bearer.jwt-token"]) is None
    assert extract_websocket_bearer_token([WS_ACCEPTED_AUTH_SUBPROTOCOL]) is None
    assert extract_websocket_bearer_token([WS_ACCEPTED_AUTH_SUBPROTOCOL, "bearer."]) is None


def test_websocket_auth_contract_defines_denial_close_codes() -> None:
    assert WS_MISSING_CREDENTIAL_CLOSE_CODE == 4401
    assert WS_INVALID_CREDENTIAL_CLOSE_CODE == 4403


def test_websocket_auth_contract_rejects_query_string_token_transport() -> None:
    assert websocket_auth_uses_query_token() is False


def test_websocket_auth_contract_defines_subscription_authorization_boundary() -> None:
    assert (
        websocket_authorization_boundary()
        == "authenticate_at_handshake_authorize_at_subscription"
    )


def test_websocket_auth_contract_does_not_add_websocket_routes_or_dispatchers() -> None:
    app = create_app()
    websocket_or_realtime_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and ("websocket" in route.path or "realtime" in route.path or "/ws" in route.path)
    ]

    assert websocket_or_realtime_routes == []
