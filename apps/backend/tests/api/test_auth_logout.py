"""Integration tests for backend logout and refresh-token revocation behavior."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.app import create_app
from taskmaster_backend.core import config as config_module
from taskmaster_backend.db.base import Base
from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.identity.models import User
from taskmaster_backend.identity.passwords import hash_password


@pytest.fixture()
def auth_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("TASKMASTER_JWT_SECRET", "test-secret-value-with-32-plus-bytes")
    monkeypatch.setenv("TASKMASTER_JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("TASKMASTER_JWT_ISSUER", "test-issuer")
    monkeypatch.setenv("TASKMASTER_JWT_AUDIENCE", "test-audience")
    monkeypatch.setenv("TASKMASTER_JWT_ACCESS_TOKEN_TTL_SECONDS", "900")
    monkeypatch.setenv("TASKMASTER_REFRESH_TOKEN_TTL_SECONDS", "3600")
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
        yield client


def test_logout_revokes_refresh_token_and_blocks_followup_refresh(
    auth_client: TestClient,
) -> None:
    login_response = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "person@example.com", "password": "secret"},
    )
    refresh_token = login_response.json()["refresh_token"]

    logout_response = auth_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert logout_response.status_code == 200
    assert logout_response.json() == {"revoked": True}

    refresh_response = auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 401
    assert refresh_response.json()["error_code"] == "revoked_session"


def test_logout_returns_invalid_session_for_unknown_refresh_token(
    auth_client: TestClient,
) -> None:
    response = auth_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "missing-refresh-token"},
    )

    assert response.status_code == 401
    assert response.json()["error_code"] == "invalid_session"
