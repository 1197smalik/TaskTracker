"""Tests for organization creation endpoint behavior."""

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
from taskmaster_backend.identity.models import Organization, User
from taskmaster_backend.identity.passwords import hash_password
from taskmaster_backend.identity.tokens import create_access_token


@pytest.fixture()
def organization_client(
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
        session.add(
            User(
                id="user-123",
                email="person@example.com",
                password_hash=hash_password("secret"),
            )
        )
        session.commit()

    with TestClient(app) as client:
        yield client, session_factory


def test_organization_create_route_is_registered() -> None:
    app = create_app()
    paths = {
        route.path: route.methods
        for route in app.routes
        if isinstance(route, APIRoute) and route.path == "/api/v1/organizations"
    }

    assert paths["/api/v1/organizations"] == {"POST"}


def test_create_organization_requires_authenticated_principal(
    organization_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = organization_client

    response = client.post("/api/v1/organizations", json={"name": "Acme"})

    assert response.status_code == 401
    assert response.json()["detail"]["error_code"] == "missing_bearer_token"


def test_create_organization_persists_trimmed_name_and_returns_typed_response(
    organization_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = organization_client

    response = client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {create_access_token('user-123')}"},
        json={"name": "  Acme Product  "},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["organization"]["id"] != ""
    assert body["organization"]["name"] == "Acme Product"
    assert body["organization"]["created_at"] != ""
    assert body["organization"]["updated_at"] != ""

    with session_factory() as session:
        organizations = session.scalars(select(Organization)).all()

    assert len(organizations) == 1
    assert organizations[0].name == "Acme Product"


def test_create_organization_returns_field_errors_for_invalid_name(
    organization_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = organization_client

    response = client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {create_access_token('user-123')}"},
        json={"name": "  "},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error_code"] == "invalid_organization_name"
    assert body["field_errors"] == {"name": ["Enter an organization name."]}
    assert body["correlation_id"] != ""


def test_create_organization_rejects_duplicate_names_using_backend_response_data(
    organization_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = organization_client
    with session_factory() as session:
        session.add(Organization(id="org-1", name="Acme"))
        session.commit()

    response = client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {create_access_token('user-123')}"},
        json={"name": " acme "},
    )

    assert response.status_code == 409
    body = response.json()
    assert body["error_code"] == "duplicate_organization_name"
    assert body["message"] == "Organization name is already in use."
    assert body["field_errors"] == {
        "name": ["Choose a different organization name."],
    }
