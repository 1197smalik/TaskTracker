"""Prometheus metric definitions and helpers."""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Histogram

from taskmaster_backend.core.metrics_contract import (
    PROMETHEUS_BASELINE_METRICS,
    PROMETHEUS_HTTP_LABELS,
)

METRICS_REGISTRY = CollectorRegistry(auto_describe=True)

HTTP_REQUESTS_TOTAL = Counter(
    PROMETHEUS_BASELINE_METRICS[0],
    "Total completed HTTP requests.",
    labelnames=PROMETHEUS_HTTP_LABELS,
    registry=METRICS_REGISTRY,
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    PROMETHEUS_BASELINE_METRICS[1],
    "HTTP request duration in seconds.",
    labelnames=PROMETHEUS_HTTP_LABELS,
    registry=METRICS_REGISTRY,
)
BACKGROUND_JOBS_TOTAL = Counter(
    PROMETHEUS_BASELINE_METRICS[2],
    "Total completed background jobs.",
    registry=METRICS_REGISTRY,
)
BACKGROUND_JOB_DURATION_SECONDS = Histogram(
    PROMETHEUS_BASELINE_METRICS[3],
    "Background job duration in seconds.",
    registry=METRICS_REGISTRY,
)


def observe_http_request(
    *,
    method: str,
    route_template: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    labels = {
        "method": method,
        "route_template": route_template,
        "status_code": str(status_code),
    }
    HTTP_REQUESTS_TOTAL.labels(**labels).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(**labels).observe(max(duration_seconds, 0.0))
