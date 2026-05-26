"""Tests for API token generation and hashing helpers."""

from __future__ import annotations

import re

import pytest

from taskmaster_backend.identity.api_tokens import (
    generate_api_token,
    hash_api_token,
    verify_api_token,
)


def test_generate_api_token_returns_high_entropy_urlsafe_material() -> None:
    token = generate_api_token()

    assert len(token) >= 32
    assert re.fullmatch(r"[A-Za-z0-9_-]+", token) is not None


def test_generate_api_token_returns_distinct_values() -> None:
    first_token = generate_api_token()
    second_token = generate_api_token()

    assert first_token != second_token


def test_hash_api_token_returns_non_plaintext_deterministic_hash() -> None:
    token = "tm-test-token-value"

    first_hash = hash_api_token(token)
    second_hash = hash_api_token(token)

    assert first_hash == second_hash
    assert first_hash != token
    assert first_hash.startswith("sha256$")
    assert token not in first_hash


def test_verify_api_token_accepts_matching_token() -> None:
    token = generate_api_token()
    token_hash = hash_api_token(token)

    assert verify_api_token(token, token_hash) is True


def test_verify_api_token_rejects_non_matching_token() -> None:
    token_hash = hash_api_token("tm-test-token-value")

    assert verify_api_token("wrong-token-value", token_hash) is False


def test_verify_api_token_rejects_invalid_hash_format() -> None:
    assert verify_api_token("tm-test-token-value", "not-a-valid-hash") is False
    assert verify_api_token("tm-test-token-value", "sha512$abc") is False
    assert verify_api_token("tm-test-token-value", "sha256$") is False


def test_hash_api_token_rejects_empty_token() -> None:
    with pytest.raises(ValueError, match="token is required"):
        hash_api_token("")


def test_verify_api_token_rejects_empty_token_without_hashing() -> None:
    assert verify_api_token("", hash_api_token("tm-test-token-value")) is False
