"""Tests for structured request logging middleware."""

from __future__ import annotations

import json
import logging

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from taskmaster_backend.app import create_app
from taskmaster_backend.core.logging_middleware import REQUEST_LOGGER_NAME


def _build_test_client(*, with_error_route: bool = False) -> TestClient:
    app = create_app()

    if with_error_route:
        router = APIRouter()

        @router.get("/boom")
        def boom() -> dict[str, str]:
            raise RuntimeError("boom")

        app.include_router(router, prefix="/api/v1")

    return TestClient(app, raise_server_exceptions=not with_error_route)


def _last_request_log(caplog: pytest.LogCaptureFixture) -> dict[str, object]:
    record = next(
        record
        for record in reversed(caplog.records)
        if record.name == REQUEST_LOGGER_NAME
    )
    return json.loads(record.getMessage())


def test_structured_logging_middleware_logs_completed_request(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = _build_test_client()

    with caplog.at_level(logging.INFO, logger=REQUEST_LOGGER_NAME):
        response = client.get("/api/v1/health")

    assert response.status_code == 200

    payload = _last_request_log(caplog)
    assert payload["event"] == "http.request.completed"
    assert payload["method"] == "GET"
    assert payload["path"] == "/api/v1/health"
    assert payload["route"] == "/api/v1/health"
    assert payload["status_code"] == 200
    assert payload["error_classification"] is None
    assert isinstance(payload["correlation_id"], str)
    assert payload["correlation_id"] != ""
    assert payload["actor_id"] is None
    assert payload["workspace_id"] is None
    assert payload["project_id"] is None
    assert isinstance(payload["latency_ms"], float)
    assert payload["latency_ms"] >= 0


def test_structured_logging_middleware_logs_server_errors(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = _build_test_client(with_error_route=True)

    with caplog.at_level(logging.INFO, logger=REQUEST_LOGGER_NAME):
        response = client.get("/api/v1/boom")

    assert response.status_code == 500

    payload = _last_request_log(caplog)
    assert payload["event"] == "http.request.failed"
    assert payload["method"] == "GET"
    assert payload["path"] == "/api/v1/boom"
    assert payload["route"] == "/api/v1/boom"
    assert payload["status_code"] == 500
    assert payload["error_classification"] == "server_error"
    assert isinstance(payload["correlation_id"], str)
    assert payload["correlation_id"] != ""
    assert payload["exception_type"] == "RuntimeError"
    assert "boom" not in payload


def test_structured_logging_middleware_does_not_log_query_or_headers(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = _build_test_client()

    with caplog.at_level(logging.INFO, logger=REQUEST_LOGGER_NAME):
        response = client.get(
            "/api/v1/health?token=secret",
            headers={"Authorization": "Bearer secret-token"},
        )

    assert response.status_code == 200

    payload = _last_request_log(caplog)
    assert payload["path"] == "/api/v1/health"
    assert "query" not in payload
    assert "headers" not in payload
    assert "authorization" not in payload
