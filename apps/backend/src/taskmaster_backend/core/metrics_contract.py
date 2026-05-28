"""Prometheus metrics exposure contract.

This module intentionally defines names and guardrails only. TM-093 owns the
actual endpoint and collection implementation.
"""

from __future__ import annotations

METRICS_ENDPOINT_PATH = "/metrics"
METRICS_EXPOSURE_POLICY = "internal_only_deployment_boundary"

PROMETHEUS_BASELINE_METRICS = (
    "taskmaster_http_requests_total",
    "taskmaster_http_request_duration_seconds",
    "taskmaster_background_jobs_total",
    "taskmaster_background_job_duration_seconds",
)

PROMETHEUS_HTTP_LABELS = (
    "method",
    "route_template",
    "status_code",
)

PROMETHEUS_FORBIDDEN_LABELS = frozenset(
    {
        "raw_path",
        "query_string",
        "user_id",
        "email",
        "token",
        "authorization",
        "correlation_id",
    }
)
