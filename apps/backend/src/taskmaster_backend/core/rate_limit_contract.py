"""Auth endpoint rate limit policy contract.

This module defines the TM-096 implementation target only. It intentionally
does not perform rate limiting, persist counters, or wire middleware.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AUTH_RATE_LIMITED_ENDPOINTS = (
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
)

RATE_LIMIT_STATUS_CODE = 429
RATE_LIMIT_ERROR_CODE = "rate_limit_exceeded"
RATE_LIMIT_RETRY_AFTER_HEADER = "Retry-After"
RATE_LIMIT_RETRY_AFTER_BODY_FIELD = "retry_after_seconds"

RATE_LIMIT_BACKING_STORE = "in_memory_process_local"
RATE_LIMIT_PRODUCTION_STORE_TARGET = "redis_distributed"
RATE_LIMIT_APPLIES_TO_CURRENT_AUTH_STUBS = True


RateLimitKeyPart = Literal[
    "client_ip",
    "normalized_email",
    "refresh_token_hash_prefix",
]


@dataclass(frozen=True)
class AuthRateLimitPolicy:
    name: Literal["login", "refresh"]
    endpoint_path: str
    attempts: int
    window_seconds: int
    key_parts: tuple[RateLimitKeyPart, ...]
    fallback_key_parts: tuple[RateLimitKeyPart, ...]


LOGIN_RATE_LIMIT_POLICY = AuthRateLimitPolicy(
    name="login",
    endpoint_path="/api/v1/auth/login",
    attempts=5,
    window_seconds=60,
    key_parts=("client_ip", "normalized_email"),
    fallback_key_parts=("client_ip",),
)

REFRESH_RATE_LIMIT_POLICY = AuthRateLimitPolicy(
    name="refresh",
    endpoint_path="/api/v1/auth/refresh",
    attempts=30,
    window_seconds=60,
    key_parts=("client_ip", "refresh_token_hash_prefix"),
    fallback_key_parts=("client_ip",),
)

AUTH_RATE_LIMIT_POLICIES = (
    LOGIN_RATE_LIMIT_POLICY,
    REFRESH_RATE_LIMIT_POLICY,
)

RATE_LIMIT_RESPONSE_CONTRACT = {
    "status_code": RATE_LIMIT_STATUS_CODE,
    "error_code": RATE_LIMIT_ERROR_CODE,
    "retry_after_body_field": RATE_LIMIT_RETRY_AFTER_BODY_FIELD,
    "retry_after_header": RATE_LIMIT_RETRY_AFTER_HEADER,
}

