"""Realtime WebSocket routes."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from taskmaster_backend.realtime.auth import authenticate_websocket_credential
from taskmaster_backend.realtime.auth_contract import (
    WS_ACCEPTED_AUTH_SUBPROTOCOL,
    WS_INVALID_CREDENTIAL_CLOSE_CODE,
    WS_MISSING_CREDENTIAL_CLOSE_CODE,
    extract_websocket_bearer_token,
)

router = APIRouter(tags=["realtime"])


@router.websocket("/ws")
async def websocket_authentication_handshake(websocket: WebSocket) -> None:
    """Authenticate a WebSocket connection without authorizing subscriptions."""
    credential = extract_websocket_bearer_token(
        list(websocket.scope.get("subprotocols", []))
    )
    if credential is None:
        await websocket.close(code=WS_MISSING_CREDENTIAL_CLOSE_CODE)
        return

    principal = authenticate_websocket_credential(credential)
    if principal is None:
        await websocket.close(code=WS_INVALID_CREDENTIAL_CLOSE_CODE)
        return

    await websocket.accept(subprotocol=WS_ACCEPTED_AUTH_SUBPROTOCOL)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
