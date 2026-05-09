"""Tests for FastAPI bearer-token authentication dependency."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from taskmaster_backend.core import config as config_module
from taskmaster_backend.identity.dependencies import get_current_principal
from taskmaster_backend.identity.tokens import create_access_token

TEST_JWT_SECRET = "test-secret-value-with-32-plus-bytes"
WRONG_TEST_JWT_SECRET = "wrong-secret-value-with-32-plus-bytes"


def test_get_current_principal_accepts_valid_bearer_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_test_jwt_settings(monkeypatch, ttl_seconds=900)
    token = create_access_token("user-123")

    principal = get_current_principal(_bearer_credentials(token))

    assert principal.subject == "user-123"
    assert principal.issuer == "test-issuer"
    assert principal.audience == "test-audience"
    assert principal.expires_at > 0


def test_get_current_principal_rejects_missing_token() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_current_principal(None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
    assert _error_detail(exc_info.value)["error_code"] == "missing_bearer_token"


def test_get_current_principal_rejects_malformed_token() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_current_principal(_bearer_credentials("not-a-jwt"))

    assert exc_info.value.status_code == 401
    assert _error_detail(exc_info.value)["error_code"] == "invalid_bearer_token"


def test_get_current_principal_rejects_expired_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_test_jwt_settings(monkeypatch, ttl_seconds=900)
    token = jwt.encode(
        {
            "sub": "user-123",
            "exp": datetime.now(UTC) - timedelta(seconds=1),
            "iss": "test-issuer",
            "aud": "test-audience",
        },
        TEST_JWT_SECRET,
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_principal(_bearer_credentials(token))

    assert exc_info.value.status_code == 401
    assert _error_detail(exc_info.value)["error_code"] == "invalid_bearer_token"


def test_get_current_principal_rejects_invalid_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_test_jwt_settings(monkeypatch, ttl_seconds=900)
    token = jwt.encode(
        {
            "sub": "user-123",
            "exp": datetime.now(UTC) + timedelta(minutes=15),
            "iss": "test-issuer",
            "aud": "test-audience",
        },
        WRONG_TEST_JWT_SECRET,
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_principal(_bearer_credentials(token))

    assert exc_info.value.status_code == 401
    assert _error_detail(exc_info.value)["error_code"] == "invalid_bearer_token"


def _set_test_jwt_settings(monkeypatch: pytest.MonkeyPatch, *, ttl_seconds: int) -> None:
    monkeypatch.setenv("TASKMASTER_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setenv("TASKMASTER_JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("TASKMASTER_JWT_ISSUER", "test-issuer")
    monkeypatch.setenv("TASKMASTER_JWT_AUDIENCE", "test-audience")
    monkeypatch.setenv("TASKMASTER_JWT_ACCESS_TOKEN_TTL_SECONDS", str(ttl_seconds))
    config_module.reset_settings_cache()


def _bearer_credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


def _error_detail(exc: HTTPException) -> dict[str, Any]:
    return cast(dict[str, Any], exc.detail)
