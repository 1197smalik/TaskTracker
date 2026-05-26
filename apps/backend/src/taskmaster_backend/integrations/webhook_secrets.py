"""Contracts for webhook secret storage and retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class WebhookSecretCreateResult:
    """Create-time secret contract.

    The raw secret is returned once to the management caller. The database stores
    only a hash for integrity/reference checks and a reference for future signing.
    """

    raw_secret: str
    secret_hash: str
    secret_reference: str


@dataclass(frozen=True, slots=True)
class WebhookSecretRotationResult:
    """Rotation contract for future management endpoints."""

    raw_secret: str
    secret_hash: str
    secret_reference: str


class WebhookSecretProvider(Protocol):
    """Secret material provider for outbound webhook signing.

    Implementations may read from encrypted storage or a secret manager. They
    must not derive signing material from the webhook endpoint's secret hash.
    """

    def get_signing_secret(self, secret_reference: str) -> str:
        """Return raw signing material for one webhook secret reference."""


def webhook_secret_response_is_return_once() -> bool:
    """Document that raw webhook secrets are returned only at create/rotation time."""
    return True


def secret_hash_is_signing_material() -> bool:
    """Document that one-way secret hashes must not be used as HMAC keys."""
    return False
