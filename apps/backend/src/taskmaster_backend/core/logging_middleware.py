"""Structured request logging middleware."""

from __future__ import annotations

import json
import logging
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request

from taskmaster_backend.core.metrics import observe_http_request

REQUEST_LOGGER_NAME = "taskmaster_backend.http"

logger = logging.getLogger(REQUEST_LOGGER_NAME)


def add_structured_logging_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def structured_logging_middleware(request: Request, call_next: Any) -> Any:
        start = perf_counter()
        request.state.correlation_id = request.headers.get("x-correlation-id") or str(
            uuid4()
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            route_template = _resolve_route_template(request)
            duration_seconds = perf_counter() - start
            observe_http_request(
                method=request.method,
                route_template=route_template,
                status_code=500,
                duration_seconds=duration_seconds,
            )
            _log_request(
                request=request,
                route_path=route_template,
                status_code=500,
                latency_ms=duration_seconds * 1000,
                event="http.request.failed",
                error_classification="server_error",
                exception_type=type(exc).__name__,
            )
            raise

        route_template = _resolve_route_template(request)
        duration_seconds = perf_counter() - start
        response.headers["X-Correlation-ID"] = request.state.correlation_id
        observe_http_request(
            method=request.method,
            route_template=route_template,
            status_code=response.status_code,
            duration_seconds=duration_seconds,
        )
        _log_request(
            request=request,
            route_path=route_template,
            status_code=response.status_code,
            latency_ms=duration_seconds * 1000,
            event="http.request.completed",
            error_classification=_classify_status(response.status_code),
            exception_type=None,
        )
        return response


def _log_request(
    *,
    request: Request,
    route_path: str,
    status_code: int,
    latency_ms: float,
    event: str,
    error_classification: str | None,
    exception_type: str | None,
) -> None:
    payload: dict[str, object | None] = {
        "event": event,
        "method": request.method,
        "path": request.url.path,
        "route": route_path,
        "status_code": status_code,
        "latency_ms": round(latency_ms, 3),
        "correlation_id": getattr(request.state, "correlation_id", None),
        "actor_id": None,
        "workspace_id": None,
        "project_id": None,
        "error_classification": error_classification,
    }
    if exception_type is not None:
        payload["exception_type"] = exception_type

    logger.info(json.dumps(payload, sort_keys=True))


def _classify_status(status_code: int) -> str | None:
    if status_code >= 500:
        return "server_error"
    if status_code >= 400:
        return "client_error"
    return None


def _resolve_route_template(request: Request) -> str:
    resolved_route = request.scope.get("route")
    route_path = getattr(resolved_route, "path", None)
    if isinstance(route_path, str):
        return route_path
    return "__unmatched__"
