"""Tests for JWT access token creation and validation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from taskmaster_backend.core import config as config_module
from taskmaster_backend.identity.tokens import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
)

TEST_JWT_SECRET = "test-secret-value-with-32-plus-bytes"
WRONG_TEST_JWT_SECRET = "wrong-secret-value-with-32-plus-bytes"


def test_create_access_token_includes_required_claims(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_test_jwt_settings(monkeypatch, ttl_seconds=900)

    token = create_access_token("user-123")
    claims = decode_access_token(token)

    assert claims.sub == "user-123"
    assert claims.iss == "test-issuer"
    assert claims.aud == "test-audience"
    assert claims.exp > 0


def test_decode_access_token_rejects_expired_token(monkeypatch: pytest.MonkeyPatch) -> None:
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

    with pytest.raises(InvalidTokenError, match="expired"):
        decode_access_token(token)


def test_decode_access_token_rejects_malformed_token() -> None:
    with pytest.raises(InvalidTokenError, match="Malformed"):
        decode_access_token("not-a-jwt")


def test_decode_access_token_rejects_token_with_invalid_signature(
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

    with pytest.raises(InvalidTokenError, match="signature"):
        decode_access_token(token)


def test_decode_access_token_rejects_missing_subject_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_test_jwt_settings(monkeypatch, ttl_seconds=900)

    token = jwt.encode(
        {
            "exp": datetime.now(UTC) + timedelta(minutes=15),
            "iss": "test-issuer",
            "aud": "test-audience",
        },
        TEST_JWT_SECRET,
        algorithm="HS256",
    )

    with pytest.raises(InvalidTokenError, match="subject"):
        decode_access_token(token)


def _set_test_jwt_settings(monkeypatch: pytest.MonkeyPatch, *, ttl_seconds: int) -> None:
    monkeypatch.setenv("TASKMASTER_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setenv("TASKMASTER_JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("TASKMASTER_JWT_ISSUER", "test-issuer")
    monkeypatch.setenv("TASKMASTER_JWT_AUDIENCE", "test-audience")
    monkeypatch.setenv("TASKMASTER_JWT_ACCESS_TOKEN_TTL_SECONDS", str(ttl_seconds))
    config_module.reset_settings_cache()
