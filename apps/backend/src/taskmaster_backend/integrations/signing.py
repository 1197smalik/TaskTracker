"""Webhook payload signing service."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Final

from taskmaster_backend.integrations.webhook_secrets import WebhookSecretProvider

WEBHOOK_SIGNATURE_ALGORITHM: Final = "sha256"


@dataclass(frozen=True, slots=True)
class WebhookSignature:
    """HMAC signature value for one outbound webhook payload."""

    algorithm: str
    digest: str

    @property
    def header_value(self) -> str:
        return f"{self.algorithm}={self.digest}"


def sign_webhook_payload(
    *,
    secret_provider: WebhookSecretProvider,
    secret_reference: str,
    payload: bytes,
) -> WebhookSignature:
    """Sign serialized webhook payload bytes using referenced secret material."""
    _require_non_empty(secret_reference, "secret_reference")
    signing_secret = secret_provider.get_signing_secret(secret_reference)
    _require_non_empty(signing_secret, "signing_secret")

    digest = hmac.new(
        signing_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return WebhookSignature(
        algorithm=WEBHOOK_SIGNATURE_ALGORITHM,
        digest=digest,
    )


def _require_non_empty(value: str, field_name: str) -> None:
    if value.strip() == "":
        raise ValueError(f"{field_name} is required")
