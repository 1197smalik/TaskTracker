"""Tests for workspace creation endpoint behavior."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.app import create_app
from taskmaster_backend.core import config as config_module
from taskmaster_backend.db.base import Base
from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.identity.models import Organization, User, Workspace
from taskmaster_backend.identity.passwords import hash_password
from taskmaster_backend.identity.tokens import create_access_token


@pytest.fixture()
def workspace_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    monkeypatch.setenv("TASKMASTER_JWT_SECRET", "test-secret-value-with-32-plus-bytes")
    monkeypatch.setenv("TASKMASTER_JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("TASKMASTER_JWT_ISSUER", "test-issuer")
    monkeypatch.setenv("TASKMASTER_JWT_AUDIENCE", "test-audience")
    monkeypatch.setenv("TASKMASTER_JWT_ACCESS_TOKEN_TTL_SECONDS", "900")
    config_module.reset_settings_cache()

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )

    app = create_app()

    def override_db_session() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_db_session

    with session_factory() as session:
        session.add_all(
            [
                User(
                    id="user-owner",
                    email="owner@example.com",
                    password_hash=hash_password("secret"),
                ),
                User(
                    id="user-other",
                    email="other@example.com",
                    password_hash=hash_password("secret"),
                ),
                Organization(
                    id="org-1",
                    name="Acme",
                    owner_user_id="user-owner",
                ),
            ]
        )
        session.commit()

    with TestClient(app) as client:
        yield client, session_factory


def test_workspace_create_route_is_registered() -> None:
    app = create_app()
    paths = {
        route.path: route.methods
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path == "/api/v1/organizations/{organization_id}/workspaces"
    }

    assert paths["/api/v1/organizations/{organization_id}/workspaces"] == {"POST"}


def test_create_workspace_requires_authenticated_principal(
    workspace_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = workspace_client

    response = client.post(
        "/api/v1/organizations/org-1/workspaces",
        json={"name": "Platform"},
    )

    assert response.status_code == 401
    assert response.json()["detail"]["error_code"] == "missing_bearer_token"


def test_create_workspace_persists_workspace_for_owner(
    workspace_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = workspace_client

    response = client.post(
        "/api/v1/organizations/org-1/workspaces",
        headers={"Authorization": f"Bearer {create_access_token('user-owner')}"},
        json={"name": "  Platform  "},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["workspace"]["id"] != ""
    assert body["workspace"]["organization_id"] == "org-1"
    assert body["workspace"]["name"] == "Platform"
    assert body["workspace"]["created_at"] != ""
    assert body["workspace"]["updated_at"] != ""

    with session_factory() as session:
        workspaces = session.scalars(select(Workspace)).all()

    assert len(workspaces) == 1
    assert workspaces[0].organization_id == "org-1"
    assert workspaces[0].name == "Platform"


def test_create_workspace_rejects_invalid_name(
    workspace_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = workspace_client

    response = client.post(
        "/api/v1/organizations/org-1/workspaces",
        headers={"Authorization": f"Bearer {create_access_token('user-owner')}"},
        json={"name": " "},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error_code"] == "invalid_workspace_name"
    assert body["field_errors"] == {"name": ["Enter a workspace name."]}


def test_create_workspace_rejects_nonexistent_organization(
    workspace_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = workspace_client

    response = client.post(
        "/api/v1/organizations/org-missing/workspaces",
        headers={"Authorization": f"Bearer {create_access_token('user-owner')}"},
        json={"name": "Platform"},
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "organization_not_found"


def test_create_workspace_rejects_unauthorized_organization_access(
    workspace_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = workspace_client

    response = client.post(
        "/api/v1/organizations/org-1/workspaces",
        headers={"Authorization": f"Bearer {create_access_token('user-other')}"},
        json={"name": "Platform"},
    )

    assert response.status_code == 403
    body = response.json()
    assert body["error_code"] == "organization_access_denied"
    assert (
        body["message"]
        == "You are not authorized to create workspaces in this organization."
    )
