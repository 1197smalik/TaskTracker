"""Tests for organization-scoped API token management endpoints."""

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
from taskmaster_backend.identity.api_token_routes import (
    create_api_token,
    list_api_tokens,
    revoke_api_token,
)
from taskmaster_backend.identity.api_token_schemas import (
    ApiTokenCreateRequest,
    ApiTokenCreateResponse,
    ApiTokenListResponse,
    ApiTokenResponse,
)
from taskmaster_backend.identity.api_tokens import verify_api_token
from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal
from taskmaster_backend.identity.models import ApiToken, Organization, User
from taskmaster_backend.identity.permissions import API_TOKEN_MANAGE_PERMISSION
from taskmaster_backend.identity.rbac import PermissionGrant, PermissionScope


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
                User(
                    id="user-123",
                    email="user@example.com",
                    password_hash="not-a-real-hash",
                ),
            ]
        )
        session.commit()


def test_api_token_routes_are_registered_under_versioned_api() -> None:
    app = create_app()
    paths: dict[str, set[str]] = {}
    for route in app.routes:
        if isinstance(route, APIRoute) and "/api-tokens" in route.path:
            paths.setdefault(route.path, set()).update(route.methods)

    assert paths["/api/v1/organizations/{organization_id}/api-tokens"] == {
        "POST",
        "GET",
    }
    assert paths[
        "/api/v1/organizations/{organization_id}/api-tokens/{api_token_id}/revoke"
    ] == {"POST"}


def test_create_token_returns_plaintext_once_and_stores_hash_only() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        response = create_api_token(
            "org-1",
            ApiTokenCreateRequest(name="Automation", scopes=["work_item:read"]),
            session,
            _principal(),
            _api_token_manage_grants("org-1"),
        )

    assert isinstance(response, ApiTokenCreateResponse)
    assert response.token != ""
    assert response.api_token.name == "Automation"
    assert response.api_token.organization_id == "org-1"
    assert response.api_token.scopes == ["work_item:read"]

    with session_factory() as session:
        stored_token = session.scalars(select(ApiToken)).one()

    assert stored_token.token_hash != response.token
    assert response.token not in stored_token.token_hash
    assert verify_api_token(response.token, stored_token.token_hash) is True


def test_list_tokens_does_not_expose_token_secret_or_hash() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        created = create_api_token(
            "org-1",
            ApiTokenCreateRequest(name="Automation", scopes=["work_item:read"]),
            session,
            _principal(),
            _api_token_manage_grants("org-1"),
        )
        assert isinstance(created, ApiTokenCreateResponse)

    with session_factory() as session:
        response = list_api_tokens(
            "org-1",
            session,
            _principal(),
            _api_token_manage_grants("org-1"),
        )

    assert isinstance(response, ApiTokenListResponse)
    assert len(response.items) == 1
    item_dump = response.items[0].model_dump()
    assert item_dump["name"] == "Automation"
    assert "token" not in item_dump
    assert "token_hash" not in item_dump


def test_revoke_token_marks_token_revoked() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        created = create_api_token(
            "org-1",
            ApiTokenCreateRequest(name="Automation"),
            session,
            _principal(),
            _api_token_manage_grants("org-1"),
        )
        assert isinstance(created, ApiTokenCreateResponse)
        api_token_id = created.api_token.id

    with session_factory() as session:
        response = revoke_api_token(
            "org-1",
            api_token_id,
            session,
            _principal(),
            _api_token_manage_grants("org-1"),
        )

    assert isinstance(response, ApiTokenResponse)
    assert response.revoked_at is not None

    with session_factory() as session:
        stored_token = session.scalars(select(ApiToken)).one()

    assert stored_token.revoked_at is not None


def test_organization_scoping_prevents_cross_organization_access() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        created = create_api_token(
            "org-1",
            ApiTokenCreateRequest(name="Org one automation"),
            session,
            _principal(),
            _api_token_manage_grants("org-1"),
        )
        assert isinstance(created, ApiTokenCreateResponse)
        api_token_id = created.api_token.id

    with session_factory() as session:
        list_response = list_api_tokens(
            "org-2",
            session,
            _principal(),
            _api_token_manage_grants("org-2"),
        )
        revoke_response = revoke_api_token(
            "org-2",
            api_token_id,
            session,
            _principal(),
            _api_token_manage_grants("org-2"),
        )

    assert isinstance(list_response, ApiTokenListResponse)
    assert list_response.items == []
    assert isinstance(revoke_response, JSONResponse)
    assert revoke_response.status_code == 404
    assert b"api_token_not_found" in revoke_response.body


def test_api_token_management_requires_contract_permission_and_scope() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        with pytest.raises(HTTPException) as exc_info:
            create_api_token(
                "org-1",
                ApiTokenCreateRequest(name="Automation"),
                session,
                _principal(),
                _api_token_manage_grants("org-2"),
            )

    assert exc_info.value.status_code == 403
    detail = cast(dict[str, Any], exc_info.value.detail)
    assert detail["reason"] == "scope_mismatch"


def test_missing_token_returns_stable_not_found_response() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        response = revoke_api_token(
            "org-1",
            "missing-token",
            session,
            _principal(),
            _api_token_manage_grants("org-1"),
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert b"api_token_not_found" in response.body


def test_invalid_organization_scope_is_rejected() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        response = create_api_token(
            " ",
            ApiTokenCreateRequest(name="Automation"),
            session,
            _principal(),
            _api_token_manage_grants("org-1"),
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert b"invalid_organization_scope" in response.body


def test_missing_organization_returns_stable_not_found_response() -> None:
    session_factory = _create_test_session_factory()
    _seed_scope(session_factory)

    with session_factory() as session:
        response = list_api_tokens(
            "missing-org",
            session,
            _principal(),
            _api_token_manage_grants("missing-org"),
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert b"organization_not_found" in response.body


def _principal() -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        subject="user-123",
        issuer="test-issuer",
        audience="test-audience",
        expires_at=9_999_999_999,
    )


def _api_token_manage_grants(organization_id: str) -> list[PermissionGrant]:
    return [
        PermissionGrant(
            actor_id="user-123",
            permission=API_TOKEN_MANAGE_PERMISSION,
            scope=PermissionScope(scope_type="organization", scope_id=organization_id),
        )
    ]
