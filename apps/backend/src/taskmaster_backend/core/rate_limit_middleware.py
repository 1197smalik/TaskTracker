"""Auth endpoint rate limiting middleware."""

from __future__ import annotations

import hashlib
import math
from collections import deque
from threading import Lock
from time import monotonic
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from taskmaster_backend.core.rate_limit_contract import (
    AUTH_RATE_LIMIT_POLICIES,
    RATE_LIMIT_APPLIES_TO_CURRENT_AUTH_STUBS,
    RATE_LIMIT_ERROR_CODE,
    RATE_LIMIT_RETRY_AFTER_BODY_FIELD,
    RATE_LIMIT_RETRY_AFTER_HEADER,
    RATE_LIMIT_STATUS_CODE,
    AuthRateLimitPolicy,
    RateLimitKeyPart,
)


class _InMemoryRateLimitStore:
    def __init__(self) -> None:
        self._entries: dict[str, deque[float]] = {}
        self._lock = Lock()

    def check_and_record(
        self,
        *,
        key: str,
        attempts: int,
        window_seconds: int,
        now: float,
    ) -> int | None:
        with self._lock:
            timestamps = self._entries.setdefault(key, deque())
            cutoff = now - window_seconds
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            if len(timestamps) >= attempts:
                retry_after_seconds = math.ceil(window_seconds - (now - timestamps[0]))
                return max(1, retry_after_seconds)

            timestamps.append(now)
            return None

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


_PROCESS_LOCAL_RATE_LIMIT_STORE = _InMemoryRateLimitStore()
_AUTH_RATE_LIMIT_POLICIES_BY_PATH = {
    policy.endpoint_path: policy for policy in AUTH_RATE_LIMIT_POLICIES
}


def add_auth_rate_limit_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def auth_rate_limit_middleware(request: Request, call_next: Any) -> Any:
        policy = _AUTH_RATE_LIMIT_POLICIES_BY_PATH.get(request.url.path)
        if request.method != "POST" or policy is None:
            return await call_next(request)

        request.state.resolved_route_template = policy.endpoint_path

        if not RATE_LIMIT_APPLIES_TO_CURRENT_AUTH_STUBS:
            return await call_next(request)

        body = await _parse_json_body(request)
        key = _build_rate_limit_key(policy=policy, request=request, body=body)
        retry_after_seconds = _PROCESS_LOCAL_RATE_LIMIT_STORE.check_and_record(
            key=key,
            attempts=policy.attempts,
            window_seconds=policy.window_seconds,
            now=monotonic(),
        )
        if retry_after_seconds is None:
            return await call_next(request)

        correlation_id = getattr(request.state, "correlation_id", None) or str(uuid4())
        request.state.correlation_id = correlation_id
        return JSONResponse(
            status_code=RATE_LIMIT_STATUS_CODE,
            headers={RATE_LIMIT_RETRY_AFTER_HEADER: str(retry_after_seconds)},
            content={
                "error_code": RATE_LIMIT_ERROR_CODE,
                "message": "Rate limit exceeded.",
                "details": {},
                "correlation_id": correlation_id,
                "field_errors": {},
                "retry_after": retry_after_seconds,
                RATE_LIMIT_RETRY_AFTER_BODY_FIELD: retry_after_seconds,
            },
        )


def reset_process_local_rate_limit_store() -> None:
    _PROCESS_LOCAL_RATE_LIMIT_STORE.clear()


async def _parse_json_body(request: Request) -> dict[str, object] | None:
    try:
        payload = await request.json()
    except Exception:
        return None

    if isinstance(payload, dict):
        return payload
    return None


def _build_rate_limit_key(
    *,
    policy: AuthRateLimitPolicy,
    request: Request,
    body: dict[str, object] | None,
) -> str:
    key_parts = [
        _resolve_key_part_value(key_part=key_part, request=request, body=body)
        for key_part in policy.key_parts
    ]
    if any(value is None for value in key_parts):
        return _build_fallback_key(policy=policy, request=request, body=body)

    return "|".join(
        f"{key_part}={value}"
        for key_part, value in zip(policy.key_parts, key_parts, strict=True)
    )


def _build_fallback_key(
    *,
    policy: AuthRateLimitPolicy,
    request: Request,
    body: dict[str, object] | None,
) -> str:
    return "|".join(
        f"{key_part}={_resolve_key_part_value(key_part=key_part, request=request, body=body)}"
        for key_part in policy.fallback_key_parts
    )


def _resolve_key_part_value(
    *,
    key_part: RateLimitKeyPart,
    request: Request,
    body: dict[str, object] | None,
) -> str | None:
    if key_part == "client_ip":
        return request.client.host if request.client is not None else "unknown"
    if key_part == "normalized_email":
        return _normalized_email(body)
    if key_part == "refresh_token_hash_prefix":
        return _refresh_token_hash_prefix(body)
    return None


def _normalized_email(body: dict[str, object] | None) -> str | None:
    if body is None:
        return None

    email = body.get("email")
    if not isinstance(email, str):
        return None

    normalized_email = email.strip().lower()
    return normalized_email or None


def _refresh_token_hash_prefix(body: dict[str, object] | None) -> str | None:
    if body is None:
        return None

    refresh_token = body.get("refresh_token")
    if not isinstance(refresh_token, str) or refresh_token == "":
        return None

    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
