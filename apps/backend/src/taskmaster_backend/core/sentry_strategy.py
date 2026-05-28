"""Backend Sentry capture strategy and redaction policy."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from os import environ as os_environ
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

BACKEND_SENTRY_DSN_ENV_VAR = "SENTRY_DSN"
SENTRY_ENVIRONMENT_ENV_VAR = "SENTRY_ENVIRONMENT"
SENTRY_RELEASE_ENV_VAR = "SENTRY_RELEASE"

BACKEND_SENTRY_ALLOWED_CONTEXT_FIELDS = (
    "correlation_id",
    "route_template",
    "method",
    "status_code",
    "workspace_id",
    "project_id",
)
BACKEND_SENTRY_FORBIDDEN_CONTEXT_FIELDS = (
    "raw_path",
    "query_string",
    "authorization",
    "cookie",
    "set-cookie",
    "token",
    "access_token",
    "refresh_token",
    "password",
    "secret",
    "email",
    "user_id",
)


@dataclass(frozen=True)
class BackendSentryStrategy:
    enabled: bool
    dsn_env_var: str
    capture_unhandled_exceptions: bool
    send_default_pii: bool
    allowed_context_fields: tuple[str, ...]
    forbidden_context_fields: tuple[str, ...]
    environment_env_var: str
    release_env_var: str


def build_backend_sentry_strategy(
    environ: Mapping[str, str] | None = None,
) -> BackendSentryStrategy:
    runtime_environ = os_environ if environ is None else environ
    dsn = runtime_environ.get(BACKEND_SENTRY_DSN_ENV_VAR, "").strip()
    return BackendSentryStrategy(
        enabled=dsn != "",
        dsn_env_var=BACKEND_SENTRY_DSN_ENV_VAR,
        capture_unhandled_exceptions=True,
        send_default_pii=False,
        allowed_context_fields=BACKEND_SENTRY_ALLOWED_CONTEXT_FIELDS,
        forbidden_context_fields=BACKEND_SENTRY_FORBIDDEN_CONTEXT_FIELDS,
        environment_env_var=SENTRY_ENVIRONMENT_ENV_VAR,
        release_env_var=SENTRY_RELEASE_ENV_VAR,
    )


def configure_sentry(environ: Mapping[str, str] | None = None) -> BackendSentryStrategy:
    runtime_environ = os_environ if environ is None else environ
    strategy = build_backend_sentry_strategy(runtime_environ)
    if not strategy.enabled:
        return strategy

    sentry_sdk.init(
        dsn=runtime_environ[BACKEND_SENTRY_DSN_ENV_VAR],
        environment=runtime_environ.get(SENTRY_ENVIRONMENT_ENV_VAR),
        release=runtime_environ.get(SENTRY_RELEASE_ENV_VAR),
        integrations=[FastApiIntegration()],
        send_default_pii=strategy.send_default_pii,
        before_send=redact_backend_sentry_event,
    )
    return strategy


def redact_backend_sentry_event(
    event: Any,
    hint: dict[str, Any],
) -> Any:
    del hint
    return _redact_mapping(event)


def _redact_mapping(value: object) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, nested_value in value.items():
            lowered_key = key.lower()
            if lowered_key in BACKEND_SENTRY_FORBIDDEN_CONTEXT_FIELDS:
                continue
            redacted[key] = _redact_mapping(nested_value)
        return redacted
    if isinstance(value, list):
        return [_redact_mapping(item) for item in value]
    return value
