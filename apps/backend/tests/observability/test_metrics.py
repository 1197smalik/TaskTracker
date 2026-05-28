"""Tests for the Prometheus metrics endpoint."""

from __future__ import annotations

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from prometheus_client import CONTENT_TYPE_LATEST

from taskmaster_backend.app import create_app
from taskmaster_backend.core.metrics import (
    BACKGROUND_JOB_DURATION_SECONDS,
    BACKGROUND_JOBS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
)
from taskmaster_backend.core.metrics_contract import (
    METRICS_ENDPOINT_PATH,
    PROMETHEUS_BASELINE_METRICS,
    PROMETHEUS_FORBIDDEN_LABELS,
    PROMETHEUS_HTTP_LABELS,
)


def test_metrics_endpoint_is_registered_outside_versioned_api() -> None:
    app = create_app()
    metric_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute) and route.path == METRICS_ENDPOINT_PATH
    ]

    assert len(metric_routes) == 1
    assert metric_routes[0].path == "/metrics"
    assert metric_routes[0].include_in_schema is False


def test_metrics_endpoint_is_not_listed_in_openapi_schema() -> None:
    app = create_app()

    assert METRICS_ENDPOINT_PATH not in app.openapi()["paths"]


def test_metrics_endpoint_returns_prometheus_text_with_baseline_metrics() -> None:
    client = TestClient(create_app())

    response = client.get(METRICS_ENDPOINT_PATH)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(CONTENT_TYPE_LATEST)

    for metric_name in PROMETHEUS_BASELINE_METRICS:
        assert metric_name in response.text


def test_metrics_endpoint_exposes_http_samples_with_allowed_labels_only() -> None:
    client = TestClient(create_app())

    health_response = client.get("/api/v1/health")
    assert health_response.status_code == 200

    response = client.get(METRICS_ENDPOINT_PATH)

    http_counter_sample = (
        'taskmaster_http_requests_total{method="GET",'
        'route_template="/api/v1/health",status_code="200"}'
    )
    http_duration_sample = (
        'taskmaster_http_request_duration_seconds_count{method="GET",'
        'route_template="/api/v1/health",status_code="200"}'
    )

    assert http_counter_sample in response.text
    assert http_duration_sample in response.text


def test_metric_objects_reuse_contract_label_guardrails() -> None:
    http_metric_label_sets = {
        tuple(HTTP_REQUESTS_TOTAL._labelnames),
        tuple(HTTP_REQUEST_DURATION_SECONDS._labelnames),
    }
    background_metric_label_sets = {
        tuple(BACKGROUND_JOBS_TOTAL._labelnames),
        tuple(BACKGROUND_JOB_DURATION_SECONDS._labelnames),
    }

    assert http_metric_label_sets == {PROMETHEUS_HTTP_LABELS}
    assert background_metric_label_sets == {()}
    assert set(PROMETHEUS_HTTP_LABELS).isdisjoint(PROMETHEUS_FORBIDDEN_LABELS)
