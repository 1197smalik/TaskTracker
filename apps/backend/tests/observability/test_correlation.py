"""Tests for request correlation id propagation."""

from __future__ import annotations

import json
import logging

import pytest
from fastapi.testclient import TestClient

from taskmaster_backend.app import create_app
from taskmaster_backend.core.logging_middleware import REQUEST_LOGGER_NAME


def _last_request_log(caplog: pytest.LogCaptureFixture) -> dict[str, object]:
    record = next(
        record
        for record in reversed(caplog.records)
        if record.name == REQUEST_LOGGER_NAME
    )
    return json.loads(record.getMessage())


def test_correlation_id_is_generated_for_request_and_added_to_response(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = TestClient(create_app())

    with caplog.at_level(logging.INFO, logger=REQUEST_LOGGER_NAME):
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    correlation_id = response.headers["X-Correlation-ID"]
    assert correlation_id != ""

    payload = _last_request_log(caplog)
    assert payload["correlation_id"] == correlation_id


def test_correlation_id_header_is_preserved_when_provided(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = TestClient(create_app())
    correlation_id = "corr-client-supplied-123"

    with caplog.at_level(logging.INFO, logger=REQUEST_LOGGER_NAME):
        response = client.get(
            "/api/v1/health",
            headers={"X-Correlation-ID": correlation_id},
        )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == correlation_id

    payload = _last_request_log(caplog)
    assert payload["correlation_id"] == correlation_id
