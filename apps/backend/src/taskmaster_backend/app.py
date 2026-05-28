"""Application factory for the TaskMaster backend skeleton."""

from fastapi import FastAPI

from taskmaster_backend.api.metrics import router as metrics_router
from taskmaster_backend.api.router import api_router
from taskmaster_backend.core.logging_middleware import add_structured_logging_middleware
from taskmaster_backend.core.sentry_strategy import configure_sentry
from taskmaster_backend.core.tracing import add_tracing_middleware


def create_app() -> FastAPI:
    configure_sentry()
    app = FastAPI(title="TaskMaster Backend", version="0.1.0")
    add_tracing_middleware(app)
    add_structured_logging_middleware(app)
    app.include_router(metrics_router)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
