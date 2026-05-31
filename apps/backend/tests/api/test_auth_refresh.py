"""Integration tests for backend refresh-session behavior."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.app import create_app
from taskmaster_backend.core import config as config_module
from taskmaster_backend.db.base import Base
from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.identity.auth_service import hash_refresh_token
from taskmaster_backend.identity.models import RefreshToken, User
from taskmaster_backend.identity.passwords import hash_password
from taskmaster_backend.identity.tokens import decode_access_token


@pytest.fixture()
def auth_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
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
        yield client, session_factory


def test_refresh_rotates_refresh_token_and_renews_access_token(
    auth_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = auth_client
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "person@example.com", "password": "secret"},
    )
    original_refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["refresh_token"] != original_refresh_token
    claims = decode_access_token(body["access_token"])
    assert claims.sub == "user-123"

    with session_factory() as session:
        stored_tokens = session.scalars(select(RefreshToken).order_by(RefreshToken.created_at)).all()

    assert len(stored_tokens) == 2
    original_stored_token = next(
        token
        for token in stored_tokens
        if token.token_hash == hash_refresh_token(original_refresh_token)
    )
    assert original_stored_token.revoked_at is not None


def test_refresh_returns_expired_session_for_expired_refresh_token(
    auth_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = auth_client

    with session_factory() as session:
        session.add(
            RefreshToken(
                user_id="user-123",
                token_hash=hash_refresh_token("expired-refresh-token"),
                expires_at=datetime.now(UTC) - timedelta(seconds=1),
            )
        )
        session.commit()

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "expired-refresh-token"},
    )

    assert response.status_code == 401
    assert response.json()["error_code"] == "expired_session"


def test_refresh_returns_revoked_session_for_revoked_refresh_token(
    auth_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = auth_client

    with session_factory() as session:
        session.add(
            RefreshToken(
                user_id="user-123",
                token_hash=hash_refresh_token("revoked-refresh-token"),
                expires_at=datetime.now(UTC) + timedelta(hours=1),
                revoked_at=datetime.now(UTC),
            )
        )
        session.commit()

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "revoked-refresh-token"},
    )

    assert response.status_code == 401
    assert response.json()["error_code"] == "revoked_session"

