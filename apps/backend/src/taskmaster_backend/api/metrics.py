"""Prometheus metrics endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from taskmaster_backend.core.metrics import METRICS_REGISTRY
from taskmaster_backend.core.metrics_contract import METRICS_ENDPOINT_PATH

router = APIRouter(tags=["observability"])


@router.get(METRICS_ENDPOINT_PATH, include_in_schema=False)
def metrics() -> Response:
    return Response(
        content=generate_latest(METRICS_REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )
