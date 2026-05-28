"""Tests for backend Sentry capture strategy."""

from __future__ import annotations

from typing import Any

from taskmaster_backend.core import sentry_strategy
from taskmaster_backend.core.sentry_strategy import (
    BACKEND_SENTRY_ALLOWED_CONTEXT_FIELDS,
    BACKEND_SENTRY_DSN_ENV_VAR,
    BACKEND_SENTRY_FORBIDDEN_CONTEXT_FIELDS,
    build_backend_sentry_strategy,
    configure_sentry,
    redact_backend_sentry_event,
)


def test_backend_sentry_strategy_is_disabled_without_dsn() -> None:
    strategy = build_backend_sentry_strategy({})

    assert strategy.enabled is False
    assert strategy.dsn_env_var == BACKEND_SENTRY_DSN_ENV_VAR
    assert strategy.capture_unhandled_exceptions is True
    assert strategy.send_default_pii is False


def test_backend_sentry_strategy_is_enabled_with_dsn() -> None:
    strategy = build_backend_sentry_strategy(
        {BACKEND_SENTRY_DSN_ENV_VAR: "https://example@sentry.invalid/1"}
    )

    assert strategy.enabled is True
    assert strategy.allowed_context_fields == BACKEND_SENTRY_ALLOWED_CONTEXT_FIELDS
    assert strategy.forbidden_context_fields == BACKEND_SENTRY_FORBIDDEN_CONTEXT_FIELDS


def test_backend_sentry_redaction_removes_sensitive_context() -> None:
    event: dict[str, Any] = {
        "request": {
            "headers": {"Authorization": "Bearer secret", "X-Trace": "ok"},
            "query_string": "token=secret",
            "data": {"password": "hidden", "safe": "kept"},
        },
        "user": {"email": "user@example.com", "username": "kept"},
        "tags": {
            "correlation_id": "corr-123",
            "route_template": "/api/v1/health",
            "workspace_id": "ws-1",
            "project_id": "proj-1",
        },
    }

    redacted = redact_backend_sentry_event(event, {})

    assert redacted["request"]["headers"] == {"X-Trace": "ok"}
    assert "query_string" not in redacted["request"]
    assert redacted["request"]["data"] == {"safe": "kept"}
    assert redacted["user"] == {"username": "kept"}
    assert redacted["tags"]["correlation_id"] == "corr-123"
    assert redacted["tags"]["route_template"] == "/api/v1/health"


def test_configure_sentry_skips_sdk_init_when_disabled(
    monkeypatch: Any,
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_init(**kwargs: Any) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(sentry_strategy.sentry_sdk, "init", fake_init)

    strategy = configure_sentry({})

    assert strategy.enabled is False
    assert calls == []


def test_configure_sentry_initializes_sdk_with_redaction(
    monkeypatch: Any,
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_init(**kwargs: Any) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(sentry_strategy.sentry_sdk, "init", fake_init)

    strategy = configure_sentry(
        {
            BACKEND_SENTRY_DSN_ENV_VAR: "https://example@sentry.invalid/1",
            sentry_strategy.SENTRY_ENVIRONMENT_ENV_VAR: "test",
            sentry_strategy.SENTRY_RELEASE_ENV_VAR: "revamp-sha",
        }
    )

    assert strategy.enabled is True
    assert len(calls) == 1
    init_kwargs = calls[0]
    assert init_kwargs["dsn"] == "https://example@sentry.invalid/1"
    assert init_kwargs["environment"] == "test"
    assert init_kwargs["release"] == "revamp-sha"
    assert init_kwargs["send_default_pii"] is False
    assert init_kwargs["before_send"] is redact_backend_sentry_event
    assert any(
        integration.__class__.__name__ == "FastApiIntegration"
        for integration in init_kwargs["integrations"]
    )
