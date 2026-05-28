"""OpenTelemetry tracing baseline for backend HTTP requests."""

from __future__ import annotations

from typing import Any, cast

from fastapi import FastAPI, Request
from opentelemetry import propagate
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SpanProcessor
from opentelemetry.trace import Span, SpanKind, Status, StatusCode, Tracer

TRACING_SERVICE_NAME = "taskmaster-backend"
HTTP_TRACER_NAME = "taskmaster_backend.http"
TRACING_ROUTE_FALLBACK = "__unmatched__"


def configure_tracing(app: FastAPI) -> None:
    if hasattr(app.state, "tracer_provider"):
        return

    tracer_provider = TracerProvider(
        resource=Resource.create({SERVICE_NAME: TRACING_SERVICE_NAME})
    )
    app.state.tracer_provider = tracer_provider
    app.state.http_tracer = tracer_provider.get_tracer(HTTP_TRACER_NAME)


def get_tracer_provider(app: FastAPI) -> TracerProvider:
    configure_tracing(app)
    return cast(TracerProvider, app.state.tracer_provider)


def add_span_processor(app: FastAPI, span_processor: SpanProcessor) -> None:
    get_tracer_provider(app).add_span_processor(span_processor)


def add_tracing_middleware(app: FastAPI) -> None:
    configure_tracing(app)

    @app.middleware("http")
    async def tracing_middleware(request: Request, call_next: Any) -> Any:
        tracer = cast(Tracer, app.state.http_tracer)
        initial_span_name = f"{request.method} {TRACING_ROUTE_FALLBACK}"
        parent_context = propagate.extract(request.headers)

        with tracer.start_as_current_span(
            initial_span_name,
            context=parent_context,
            kind=SpanKind.SERVER,
        ) as span:
            span.set_attribute("http.request.method", request.method)

            try:
                response = await call_next(request)
            except Exception as exc:
                _update_span_route(span, request)
                span.set_attribute("http.response.status_code", 500)
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR))
                raise

            _update_span_route(span, request)
            span.set_attribute("http.response.status_code", response.status_code)
            if response.status_code >= 500:
                span.set_status(Status(StatusCode.ERROR))
            return response


def _update_span_route(span: Span, request: Request) -> None:
    route_template = _resolve_route_template(request)
    span.update_name(f"{request.method} {route_template}")
    span.set_attribute("http.route", route_template)


def _resolve_route_template(request: Request) -> str:
    resolved_route = request.scope.get("route")
    route_path = getattr(resolved_route, "path", None)
    if isinstance(route_path, str):
        return route_path
    return TRACING_ROUTE_FALLBACK
