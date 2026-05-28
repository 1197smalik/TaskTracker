"""Application factory for the TaskMaster backend skeleton."""

from fastapi import FastAPI

from taskmaster_backend.api.metrics import router as metrics_router
from taskmaster_backend.api.router import api_router
from taskmaster_backend.core.logging_middleware import add_structured_logging_middleware


def create_app() -> FastAPI:
    app = FastAPI(title="TaskMaster Backend", version="0.1.0")
    add_structured_logging_middleware(app)
    app.include_router(metrics_router)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
