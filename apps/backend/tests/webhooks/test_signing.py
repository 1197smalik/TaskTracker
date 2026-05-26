"""Tests for webhook signing service."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Final

import pytest
from fastapi.routing import APIRoute

from taskmaster_backend.app import create_app
from taskmaster_backend.integrations.signing import (
    WEBHOOK_SIGNATURE_ALGORITHM,
    sign_webhook_payload,
)

SECRET_REFERENCE: Final = "secret-ref-1"
SIGNING_SECRET: Final = "whsec_signing_material"


class StaticSecretProvider:
    def __init__(self) -> None:
        self.requested_references: list[str] = []

    def get_signing_secret(self, secret_reference: str) -> str:
        self.requested_references.append(secret_reference)
        if secret_reference != SECRET_REFERENCE:
            raise AssertionError("unexpected secret reference")
        return SIGNING_SECRET


def test_sign_webhook_payload_uses_provider_secret_reference() -> None:
    provider = StaticSecretProvider()
    payload = _payload_bytes({"event_id": "event-1", "event_type": "work_item.created"})

    signature = sign_webhook_payload(
        secret_provider=provider,
        secret_reference=SECRET_REFERENCE,
        payload=payload,
    )

    expected_digest = hmac.new(
        SIGNING_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    assert provider.requested_references == [SECRET_REFERENCE]
    assert signature.algorithm == WEBHOOK_SIGNATURE_ALGORITHM
    assert signature.digest == expected_digest
    assert signature.header_value == f"sha256={expected_digest}"


def test_sign_webhook_payload_is_deterministic_for_same_payload_and_secret() -> None:
    payload = _payload_bytes({"delivery_id": "delivery-1", "payload": {"id": "1"}})

    first_signature = sign_webhook_payload(
        secret_provider=StaticSecretProvider(),
        secret_reference=SECRET_REFERENCE,
        payload=payload,
    )
    second_signature = sign_webhook_payload(
        secret_provider=StaticSecretProvider(),
        secret_reference=SECRET_REFERENCE,
        payload=payload,
    )

    assert first_signature == second_signature


def test_sign_webhook_payload_changes_when_payload_changes() -> None:
    first_signature = sign_webhook_payload(
        secret_provider=StaticSecretProvider(),
        secret_reference=SECRET_REFERENCE,
        payload=_payload_bytes({"event_id": "event-1"}),
    )
    second_signature = sign_webhook_payload(
        secret_provider=StaticSecretProvider(),
        secret_reference=SECRET_REFERENCE,
        payload=_payload_bytes({"event_id": "event-2"}),
    )

    assert first_signature != second_signature


def test_sign_webhook_payload_rejects_missing_secret_reference() -> None:
    with pytest.raises(ValueError, match="secret_reference is required"):
        sign_webhook_payload(
            secret_provider=StaticSecretProvider(),
            secret_reference=" ",
            payload=b"{}",
        )


def test_sign_webhook_payload_rejects_provider_empty_secret() -> None:
    class EmptySecretProvider:
        def get_signing_secret(self, secret_reference: str) -> str:
            return ""

    with pytest.raises(ValueError, match="signing_secret is required"):
        sign_webhook_payload(
            secret_provider=EmptySecretProvider(),
            secret_reference=SECRET_REFERENCE,
            payload=b"{}",
        )


def test_signing_service_does_not_use_secret_hash_as_signing_material() -> None:
    provider = StaticSecretProvider()

    sign_webhook_payload(
        secret_provider=provider,
        secret_reference=SECRET_REFERENCE,
        payload=b"{}",
    )

    assert provider.requested_references == [SECRET_REFERENCE]
    assert "sha256$" not in provider.requested_references


def test_signing_service_does_not_add_delivery_or_management_routes() -> None:
    app = create_app()
    signing_or_delivery_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and ("signing" in route.path or "delivery" in route.path)
    ]

    assert signing_or_delivery_routes == []


def _payload_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
