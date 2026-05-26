"""Tests for organization-scoped webhook management endpoints."""

from __future__ import annotations

from typing import Any, cast

import pytest
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.app import create_app
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal
from taskmaster_backend.identity.models import Organization, User, Workspace
from taskmaster_backend.identity.rbac import PermissionGrant, PermissionScope
from taskmaster_backend.integrations.models import WebhookEndpoint
from taskmaster_backend.integrations.permissions import INTEGRATION_WEBHOOK_MANAGE_PERMISSION
from taskmaster_backend.integrations.routes import (
    create_webhook_endpoint,
    get_webhook_secret_issuer,
    list_webhook_endpoints,
    revoke_webhook_endpoint,
)
from taskmaster_backend.integrations.schemas import (
    WebhookEndpointCreateRequest,
    WebhookEndpointCreateResponse,
    WebhookEndpointListResponse,
    WebhookEndpointResponse,
)
from taskmaster_backend.integrations.webhook_secrets import WebhookSecretCreateResult


class StaticWebhookSecretIssuer:
    def create_webhook_secret(self, webhook_id: str) -> WebhookSecretCreateResult:
        return WebhookSecretCreateResult(
            raw_secret=f"whsec_{webhook_id}",
            secret_hash=f"sha256${webhook_id}",
            secret_reference=f"secret-ref-{webhook_id}",
        )


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def _seed_scope(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        session.add_all(
            [
                Organization(id="org-1", name="Acme"),
                Organization(id="org-2", name="Globex"),
                Workspace(id="workspace-1", organization_id="org-1", name="Platform"),
                Workspace(id="workspace-2", organization_id="org-2", name="Ops"),
                User(
                    id="user-123",
                    email="user@example.com",
                    password_hash="not-a-real-hash",
                ),
            ]
        )
        session.commit()


def test_webhook_routes_are_registered_under_versioned_api() -> None:
    app = create_app()
    paths: dict[str, set[str]] = {}
    for route in app.routes:
        if isinstance(route, APIRoute) and "/webhooks" in route.path:
            paths.setdefault(route.path, set()).update(route.methods)

    assert paths["/api/v1/organizations/{organization_id}/webhooks"] == {
        "POST",
        "GET",
    }
    assert paths[
        "/api/v1/organizations/{organization_id}/webhooks/{webhook_endpoint_id}/revoke"
    ] == {"POST"}


def test_create_webhook_returns_secret_once_and_stores_reference_not_plaintext() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        response = create_webhook_endpoint(
            "org-1",
            WebhookEndpointCreateRequest(
                url="https://example.test/webhook",
                workspace_id="workspace-1",
                event_types=["work_item.created"],
                project_filters=["project-1"],
            ),
            session,
            _principal(),
            _webhook_manage_grants("org-1"),
            StaticWebhookSecretIssuer(),
        )

    assert isinstance(response, WebhookEndpointCreateResponse)
    assert response.secret.startswith("whsec_")
    assert response.webhook_endpoint.organization_id == "org-1"
    assert response.webhook_endpoint.workspace_id == "workspace-1"
    assert response.webhook_endpoint.event_types == ["work_item.created"]

    with session_factory() as session:
        stored_webhook = session.scalars(select(WebhookEndpoint)).one()

    assert stored_webhook.secret_hash != response.secret
    assert stored_webhook.secret_reference != response.secret
    assert response.secret not in stored_webhook.secret_hash
    assert response.secret not in stored_webhook.secret_reference


def test_list_webhooks_does_not_expose_secret_hash_or_reference() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        created = create_webhook_endpoint(
            "org-1",
            WebhookEndpointCreateRequest(url="https://example.test/webhook"),
            session,
            _principal(),
            _webhook_manage_grants("org-1"),
            StaticWebhookSecretIssuer(),
        )
        assert isinstance(created, WebhookEndpointCreateResponse)

    with session_factory() as session:
        response = list_webhook_endpoints(
            "org-1",
            session,
            _principal(),
            _webhook_manage_grants("org-1"),
        )

    assert isinstance(response, WebhookEndpointListResponse)
    assert len(response.items) == 1
    item_dump = response.items[0].model_dump()
    assert item_dump["url"] == "https://example.test/webhook"
    assert "secret" not in item_dump
    assert "secret_hash" not in item_dump
    assert "secret_reference" not in item_dump


def test_revoke_webhook_marks_endpoint_inactive() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        created = create_webhook_endpoint(
            "org-1",
            WebhookEndpointCreateRequest(url="https://example.test/webhook"),
            session,
            _principal(),
            _webhook_manage_grants("org-1"),
            StaticWebhookSecretIssuer(),
        )
        assert isinstance(created, WebhookEndpointCreateResponse)
        webhook_id = created.webhook_endpoint.id

    with session_factory() as session:
        response = revoke_webhook_endpoint(
            "org-1",
            webhook_id,
            session,
            _principal(),
            _webhook_manage_grants("org-1"),
        )

    assert isinstance(response, WebhookEndpointResponse)
    assert response.is_active is False

    with session_factory() as session:
        stored_webhook = session.scalars(select(WebhookEndpoint)).one()

    assert stored_webhook.is_active is False


def test_organization_scoping_prevents_cross_organization_access() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        created = create_webhook_endpoint(
            "org-1",
            WebhookEndpointCreateRequest(url="https://example.test/webhook"),
            session,
            _principal(),
            _webhook_manage_grants("org-1"),
            StaticWebhookSecretIssuer(),
        )
        assert isinstance(created, WebhookEndpointCreateResponse)
        webhook_id = created.webhook_endpoint.id

    with session_factory() as session:
        list_response = list_webhook_endpoints(
            "org-2",
            session,
            _principal(),
            _webhook_manage_grants("org-2"),
        )
        revoke_response = revoke_webhook_endpoint(
            "org-2",
            webhook_id,
            session,
            _principal(),
            _webhook_manage_grants("org-2"),
        )

    assert isinstance(list_response, WebhookEndpointListResponse)
    assert list_response.items == []
    assert isinstance(revoke_response, JSONResponse)
    assert revoke_response.status_code == 404
    assert b"webhook_not_found" in revoke_response.body


def test_webhook_management_requires_contract_permission_and_scope() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        with pytest.raises(HTTPException) as exc_info:
            create_webhook_endpoint(
                "org-1",
                WebhookEndpointCreateRequest(url="https://example.test/webhook"),
                session,
                _principal(),
                _webhook_manage_grants("org-2"),
                StaticWebhookSecretIssuer(),
            )

    assert exc_info.value.status_code == 403
    detail = cast(dict[str, Any], exc_info.value.detail)
    assert detail["reason"] == "scope_mismatch"


def test_missing_webhook_returns_stable_not_found_response() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        response = revoke_webhook_endpoint(
            "org-1",
            "missing-webhook",
            session,
            _principal(),
            _webhook_manage_grants("org-1"),
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert b"webhook_not_found" in response.body


def test_invalid_organization_scope_is_rejected() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        response = create_webhook_endpoint(
            " ",
            WebhookEndpointCreateRequest(url="https://example.test/webhook"),
            session,
            _principal(),
            _webhook_manage_grants("org-1"),
            StaticWebhookSecretIssuer(),
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert b"invalid_organization_scope" in response.body


def test_invalid_workspace_scope_is_rejected() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        response = create_webhook_endpoint(
            "org-1",
            WebhookEndpointCreateRequest(
                url="https://example.test/webhook",
                workspace_id="workspace-2",
            ),
            session,
            _principal(),
            _webhook_manage_grants("org-1"),
            StaticWebhookSecretIssuer(),
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert b"invalid_workspace_scope" in response.body


def test_default_secret_issuer_fails_closed_without_fake_secret_manager() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        response = create_webhook_endpoint(
            "org-1",
            WebhookEndpointCreateRequest(url="https://example.test/webhook"),
            session,
            _principal(),
            _webhook_manage_grants("org-1"),
            get_webhook_secret_issuer(),
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 501
    assert b"webhook_secret_issuer_not_configured" in response.body


def _principal() -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        subject="user-123",
        issuer="test-issuer",
        audience="test-audience",
        expires_at=9_999_999_999,
    )


def _webhook_manage_grants(organization_id: str) -> list[PermissionGrant]:
    return [
        PermissionGrant(
            actor_id="user-123",
            permission=INTEGRATION_WEBHOOK_MANAGE_PERMISSION,
            scope=PermissionScope(scope_type="organization", scope_id=organization_id),
        )
    ]
