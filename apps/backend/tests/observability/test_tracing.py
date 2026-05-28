"""Tests for the OpenTelemetry tracing baseline."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import SpanKind

from taskmaster_backend.app import create_app
from taskmaster_backend.core.tracing import (
    TRACING_ROUTE_FALLBACK,
    TRACING_SERVICE_NAME,
    add_span_processor,
)


def _build_client() -> tuple[TestClient, InMemorySpanExporter]:
    app = create_app()
    exporter = InMemorySpanExporter()
    add_span_processor(app, SimpleSpanProcessor(exporter))
    return TestClient(app), exporter


def _latest_http_span(exporter: InMemorySpanExporter) -> ReadableSpan:
    spans = exporter.get_finished_spans()
    return spans[-1]


def _span_attributes(span: ReadableSpan) -> dict[str, object]:
    attributes = span.attributes
    assert attributes is not None
    return dict(attributes)


def test_tracing_records_http_server_span_with_route_template() -> None:
    client, exporter = _build_client()

    response = client.get("/api/v1/health")

    assert response.status_code == 200

    span = _latest_http_span(exporter)
    attributes = _span_attributes(span)
    assert span.name == "GET /api/v1/health"
    assert span.kind is SpanKind.SERVER
    assert span.resource.attributes["service.name"] == TRACING_SERVICE_NAME
    assert attributes["http.request.method"] == "GET"
    assert attributes["http.route"] == "/api/v1/health"
    assert attributes["http.response.status_code"] == 200


def test_tracing_extracts_traceparent_header_into_parent_context() -> None:
    client, exporter = _build_client()
    traceparent = "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01"

    response = client.get("/api/v1/health", headers={"traceparent": traceparent})

    assert response.status_code == 200

    span = _latest_http_span(exporter)
    assert span.parent is not None
    assert span.parent.trace_id == int("0123456789abcdef0123456789abcdef", 16)
    assert span.parent.span_id == int("0123456789abcdef", 16)


def test_tracing_uses_fallback_route_for_unmatched_paths() -> None:
    client, exporter = _build_client()

    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404

    span = _latest_http_span(exporter)
    attributes = _span_attributes(span)
    assert span.name == f"GET {TRACING_ROUTE_FALLBACK}"
    assert attributes["http.route"] == TRACING_ROUTE_FALLBACK


def test_current_span_is_available_inside_request_handler() -> None:
    app = create_app()
    exporter = InMemorySpanExporter()
    add_span_processor(app, SimpleSpanProcessor(exporter))
    router = APIRouter()

    @router.get("/trace-check")
    def trace_check() -> dict[str, object]:
        from opentelemetry import trace

        current_span = trace.get_current_span()
        context = current_span.get_span_context()
        return {
            "trace_id": format(context.trace_id, "032x"),
            "span_id": format(context.span_id, "016x"),
            "is_valid": context.is_valid,
        }

    app.include_router(router, prefix="/api/v1")
    client = TestClient(app)

    response = client.get("/api/v1/trace-check")

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_valid"] is True
    assert payload["trace_id"] != "00000000000000000000000000000000"
    assert payload["span_id"] != "0000000000000000"

    span = _latest_http_span(exporter)
    assert span.name == "GET /api/v1/trace-check"
