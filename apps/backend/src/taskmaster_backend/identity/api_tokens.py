"""API token generation and hashing helpers."""

from __future__ import annotations

import hashlib
import hmac
import secrets

API_TOKEN_HASH_SCHEME = "sha256"
API_TOKEN_BYTES = 32


def generate_api_token() -> str:
    """Generate high-entropy API token material for one-time display."""
    return secrets.token_urlsafe(API_TOKEN_BYTES)


def hash_api_token(token: str) -> str:
    """Hash API token material for deterministic storage lookup."""
    _require_non_empty_token(token)
    token_digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"{API_TOKEN_HASH_SCHEME}${token_digest}"


def verify_api_token(token: str, token_hash: str) -> bool:
    """Verify token material against a stored API token hash."""
    if token == "":
        return False

    try:
        scheme, expected_digest = token_hash.split("$", maxsplit=1)
    except ValueError:
        return False
    if scheme != API_TOKEN_HASH_SCHEME or expected_digest == "":
        return False

    candidate_hash = hash_api_token(token)
    return hmac.compare_digest(candidate_hash, token_hash)


def _require_non_empty_token(token: str) -> None:
    if token == "":
        raise ValueError("token is required")
