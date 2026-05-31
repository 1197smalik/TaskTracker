"""Tests for auth endpoint rate limiting middleware."""

from __future__ import annotations

import json
import logging
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.app import create_app
from taskmaster_backend.core.logging_middleware import REQUEST_LOGGER_NAME
from taskmaster_backend.core.rate_limit_contract import (
    RATE_LIMIT_ERROR_CODE,
    RATE_LIMIT_RETRY_AFTER_BODY_FIELD,
    RATE_LIMIT_RETRY_AFTER_HEADER,
)
from taskmaster_backend.core.rate_limit_middleware import (
    reset_process_local_rate_limit_store,
)
from taskmaster_backend.core.tracing import add_span_processor
from taskmaster_backend.db.base import Base
from taskmaster_backend.db.session import get_db_session


@pytest.fixture(autouse=True)
def reset_rate_limits() -> Generator[None, None, None]:
    reset_process_local_rate_limit_store()
    yield
    reset_process_local_rate_limit_store()


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


def _build_traced_client() -> tuple[TestClient, InMemorySpanExporter]:
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
    exporter = InMemorySpanExporter()
    add_span_processor(app, SimpleSpanProcessor(exporter))
    return TestClient(app), exporter


def _last_request_log(caplog: pytest.LogCaptureFixture) -> dict[str, object]:
    record = next(
        record
        for record in reversed(caplog.records)
        if record.name == REQUEST_LOGGER_NAME
    )
    return json.loads(record.getMessage())


def _latest_http_span(exporter: InMemorySpanExporter) -> ReadableSpan:
    spans = exporter.get_finished_spans()
    return spans[-1]


def test_login_endpoint_is_rate_limited_after_five_attempts() -> None:
    client = _build_client()

    responses = [
        client.post(
            "/api/v1/auth/login",
            json={"email": "person@example.com", "password": "secret"},
        )
        for _ in range(6)
    ]

    assert [response.status_code for response in responses[:5]] == [401] * 5
    final_response = responses[5]
    assert final_response.status_code == 429
    assert final_response.json()["error_code"] == RATE_LIMIT_ERROR_CODE
    assert 1 <= final_response.json()[RATE_LIMIT_RETRY_AFTER_BODY_FIELD] <= 60
    assert (
        final_response.headers[RATE_LIMIT_RETRY_AFTER_HEADER]
        == str(final_response.json()[RATE_LIMIT_RETRY_AFTER_BODY_FIELD])
    )
    assert "person@example.com" not in final_response.text
    assert "secret" not in final_response.text


def test_login_rate_limit_normalizes_email_before_keying() -> None:
    client = _build_client()

    for _ in range(4):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "person@example.com", "password": "secret"},
        )
        assert response.status_code == 401

    fifth_response = client.post(
        "/api/v1/auth/login",
        json={"email": " Person@Example.com ", "password": "secret"},
    )
    limited_response = client.post(
        "/api/v1/auth/login",
        json={"email": "person@example.com", "password": "secret"},
    )

    assert fifth_response.status_code == 401
    assert limited_response.status_code == 429


def test_login_rate_limit_is_scoped_per_normalized_email() -> None:
    client = _build_client()

    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "first@example.com", "password": "secret"},
        )
        assert response.status_code == 401

    second_identity_response = client.post(
        "/api/v1/auth/login",
        json={"email": "second@example.com", "password": "secret"},
    )

    assert second_identity_response.status_code == 401


def test_invalid_login_requests_fall_back_to_client_ip_keying() -> None:
    client = _build_client()

    responses = [
        client.post("/api/v1/auth/login", json={"password": "secret"}) for _ in range(6)
    ]

    assert [response.status_code for response in responses[:5]] == [422] * 5
    assert responses[5].status_code == 429


def test_refresh_rate_limit_is_scoped_per_token_hash_key() -> None:
    client = _build_client()

    for _ in range(30):
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "token-one"},
        )
        assert response.status_code == 401

    limited_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "token-one"},
    )
    separate_token_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "token-two"},
    )

    assert limited_response.status_code == 429
    assert separate_token_response.status_code == 401
    assert "token-one" not in limited_response.text


def test_logout_is_not_rate_limited_by_auth_middleware() -> None:
    client = _build_client()

    responses = [
        client.post("/api/v1/auth/logout", json={"refresh_token": "secret"}) for _ in range(7)
    ]

    assert {response.status_code for response in responses} == {401}


def test_rate_limited_auth_requests_preserve_safe_logging_and_tracing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client, exporter = _build_traced_client()

    with caplog.at_level(logging.INFO, logger=REQUEST_LOGGER_NAME):
        for _ in range(5):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "person@example.com", "password": "secret"},
            )
            assert response.status_code == 401

        limited_response = client.post(
            "/api/v1/auth/login",
            json={"email": "person@example.com", "password": "secret"},
        )

    assert limited_response.status_code == 429
    assert "person@example.com" not in limited_response.text
    assert "secret" not in limited_response.text

    payload = _last_request_log(caplog)
    assert payload["route"] == "/api/v1/auth/login"
    assert payload["status_code"] == 429
    assert payload["error_classification"] == "client_error"
    assert payload["correlation_id"] == limited_response.headers["X-Correlation-ID"]

    span = _latest_http_span(exporter)
    attributes = dict(span.attributes or {})
    assert span.name == "POST /api/v1/auth/login"
    assert attributes["http.route"] == "/api/v1/auth/login"
    assert attributes["http.response.status_code"] == 429
