"""Tests for the Prometheus metrics exposure contract."""

from __future__ import annotations

from fastapi.routing import APIRoute

from taskmaster_backend.app import create_app
from taskmaster_backend.core.metrics_contract import (
    METRICS_ENDPOINT_PATH,
    METRICS_EXPOSURE_POLICY,
    PROMETHEUS_BASELINE_METRICS,
    PROMETHEUS_FORBIDDEN_LABELS,
    PROMETHEUS_HTTP_LABELS,
)


def test_metrics_endpoint_path_contract_is_stable() -> None:
    assert METRICS_ENDPOINT_PATH == "/metrics"
    assert not METRICS_ENDPOINT_PATH.startswith("/api/")


def test_metrics_exposure_policy_is_explicitly_internal_only() -> None:
    assert METRICS_EXPOSURE_POLICY == "internal_only_deployment_boundary"


def test_baseline_metric_names_are_stable() -> None:
    assert PROMETHEUS_BASELINE_METRICS == (
        "taskmaster_http_requests_total",
        "taskmaster_http_request_duration_seconds",
        "taskmaster_background_jobs_total",
        "taskmaster_background_job_duration_seconds",
    )


def test_http_metric_labels_are_low_cardinality() -> None:
    assert PROMETHEUS_HTTP_LABELS == (
        "method",
        "route_template",
        "status_code",
    )


def test_high_cardinality_or_sensitive_labels_are_forbidden() -> None:
    assert {
        "raw_path",
        "query_string",
        "user_id",
        "email",
        "token",
        "authorization",
        "correlation_id",
    }.issubset(PROMETHEUS_FORBIDDEN_LABELS)
    assert set(PROMETHEUS_HTTP_LABELS).isdisjoint(PROMETHEUS_FORBIDDEN_LABELS)


def test_prometheus_metrics_endpoint_is_not_implemented_yet() -> None:
    app = create_app()
    metric_routes = [
        route.path
        for route in app.routes
        if isinstance(route, APIRoute) and route.path == METRICS_ENDPOINT_PATH
    ]

    assert metric_routes == []
