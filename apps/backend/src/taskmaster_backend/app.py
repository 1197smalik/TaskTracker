"""Application factory for the TaskMaster backend skeleton."""

from fastapi import FastAPI

from taskmaster_backend.api.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="TaskMaster Backend", version="0.1.0")
    app.include_router(health_router, prefix="/api/v1", tags=["platform"])
    return app


app = create_app()
