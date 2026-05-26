"""Tests for webhook secret storage and signing contracts."""

from __future__ import annotations

from fastapi.routing import APIRoute

from taskmaster_backend.app import create_app
from taskmaster_backend.integrations.models import WebhookEndpoint
from taskmaster_backend.integrations.webhook_secrets import (
    WebhookSecretCreateResult,
    WebhookSecretProvider,
    WebhookSecretRotationResult,
    secret_hash_is_signing_material,
    webhook_secret_response_is_return_once,
)


def test_plaintext_webhook_secret_is_never_stored_in_webhook_endpoint() -> None:
    columns = WebhookEndpoint.__table__.columns

    assert "secret_hash" in columns
    assert "secret_reference" in columns
    assert "secret" not in columns
    assert "raw_secret" not in columns
    assert "plaintext_secret" not in columns


def test_create_time_secret_contract_is_return_once() -> None:
    result = WebhookSecretCreateResult(
        raw_secret="whsec_raw_once",
        secret_hash="sha256$hash",
        secret_reference="secret-ref-1",
    )

    assert result.raw_secret == "whsec_raw_once"
    assert result.secret_hash == "sha256$hash"
    assert result.secret_reference == "secret-ref-1"
    assert webhook_secret_response_is_return_once() is True


def test_rotation_contract_is_design_only_and_return_once() -> None:
    result = WebhookSecretRotationResult(
        raw_secret="whsec_rotated_once",
        secret_hash="sha256$rotated",
        secret_reference="secret-ref-2",
    )

    assert result.raw_secret == "whsec_rotated_once"
    assert result.secret_reference == "secret-ref-2"
    assert webhook_secret_response_is_return_once() is True


def test_outbound_signing_requires_secret_provider_reference_contract() -> None:
    class StaticSecretProvider:
        def get_signing_secret(self, secret_reference: str) -> str:
            assert secret_reference == "secret-ref-1"
            return "whsec_signing_material"

    provider: WebhookSecretProvider = StaticSecretProvider()

    assert provider.get_signing_secret("secret-ref-1") == "whsec_signing_material"


def test_secret_hash_is_not_treated_as_signing_material() -> None:
    assert secret_hash_is_signing_material() is False


def test_webhook_secret_contract_does_not_add_management_endpoints() -> None:
    app = create_app()
    webhook_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute) and "webhook" in route.path
    ]

    assert webhook_routes == []


def test_webhook_secret_contract_does_not_add_delivery_or_signing_worker() -> None:
    app = create_app()
    worker_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and ("delivery" in route.path or "signing" in route.path)
    ]

    assert worker_routes == []
