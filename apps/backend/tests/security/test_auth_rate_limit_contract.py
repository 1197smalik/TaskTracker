"""Tests for the auth endpoint rate limit policy contract."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.app import create_app
from taskmaster_backend.core.rate_limit_contract import (
    AUTH_RATE_LIMIT_POLICIES,
    AUTH_RATE_LIMITED_ENDPOINTS,
    LOGIN_RATE_LIMIT_POLICY,
    RATE_LIMIT_APPLIES_TO_CURRENT_AUTH_STUBS,
    RATE_LIMIT_BACKING_STORE,
    RATE_LIMIT_ERROR_CODE,
    RATE_LIMIT_PRODUCTION_STORE_TARGET,
    RATE_LIMIT_RESPONSE_CONTRACT,
    RATE_LIMIT_RETRY_AFTER_BODY_FIELD,
    RATE_LIMIT_RETRY_AFTER_HEADER,
    RATE_LIMIT_STATUS_CODE,
    REFRESH_RATE_LIMIT_POLICY,
)
from taskmaster_backend.db.base import Base
from taskmaster_backend.db.session import get_db_session


def _build_client() -> TestClient:
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

    def override_db_session() -> Session:
        return session_factory()

    app.dependency_overrides[get_db_session] = override_db_session
    return TestClient(app)


def test_auth_rate_limited_endpoint_coverage_is_stable() -> None:
    assert AUTH_RATE_LIMITED_ENDPOINTS == (
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
    )
    assert {policy.endpoint_path for policy in AUTH_RATE_LIMIT_POLICIES} == set(
        AUTH_RATE_LIMITED_ENDPOINTS
    )


def test_login_rate_limit_policy_is_stable() -> None:
    assert LOGIN_RATE_LIMIT_POLICY.name == "login"
    assert LOGIN_RATE_LIMIT_POLICY.endpoint_path == "/api/v1/auth/login"
    assert LOGIN_RATE_LIMIT_POLICY.attempts == 5
    assert LOGIN_RATE_LIMIT_POLICY.window_seconds == 60
    assert LOGIN_RATE_LIMIT_POLICY.key_parts == ("client_ip", "normalized_email")
    assert LOGIN_RATE_LIMIT_POLICY.fallback_key_parts == ("client_ip",)


def test_refresh_rate_limit_policy_is_stable() -> None:
    assert REFRESH_RATE_LIMIT_POLICY.name == "refresh"
    assert REFRESH_RATE_LIMIT_POLICY.endpoint_path == "/api/v1/auth/refresh"
    assert REFRESH_RATE_LIMIT_POLICY.attempts == 30
    assert REFRESH_RATE_LIMIT_POLICY.window_seconds == 60
    assert REFRESH_RATE_LIMIT_POLICY.key_parts == (
        "client_ip",
        "refresh_token_hash_prefix",
    )
    assert REFRESH_RATE_LIMIT_POLICY.fallback_key_parts == ("client_ip",)


def test_backing_store_contract_is_stable() -> None:
    assert RATE_LIMIT_BACKING_STORE == "in_memory_process_local"
    assert RATE_LIMIT_PRODUCTION_STORE_TARGET == "redis_distributed"


def test_rate_limited_response_contract_is_stable() -> None:
    assert RATE_LIMIT_STATUS_CODE == 429
    assert RATE_LIMIT_ERROR_CODE == "rate_limit_exceeded"
    assert RATE_LIMIT_RETRY_AFTER_BODY_FIELD == "retry_after_seconds"
    assert RATE_LIMIT_RETRY_AFTER_HEADER == "Retry-After"
    assert RATE_LIMIT_RESPONSE_CONTRACT == {
        "status_code": 429,
        "error_code": "rate_limit_exceeded",
        "retry_after_body_field": "retry_after_seconds",
        "retry_after_header": "Retry-After",
    }


def test_current_contract_only_auth_endpoints_are_in_rate_limit_scope() -> None:
    assert RATE_LIMIT_APPLIES_TO_CURRENT_AUTH_STUBS is True


def test_tm096_rate_limit_middleware_protects_current_auth_endpoints() -> None:
    client = _build_client()
    login_responses = [
        client.post(
            "/api/v1/auth/login",
            json={"email": "person@example.com", "password": "secret"},
        )
        for _ in range(LOGIN_RATE_LIMIT_POLICY.attempts + 1)
    ]

    assert [response.status_code for response in login_responses[:5]] == [401] * 5
    limited_response = login_responses[5]
    assert limited_response.status_code == RATE_LIMIT_STATUS_CODE
    assert RATE_LIMIT_RETRY_AFTER_HEADER in limited_response.headers
