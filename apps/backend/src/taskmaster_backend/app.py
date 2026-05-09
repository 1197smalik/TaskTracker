"""Application factory for the TaskMaster backend skeleton."""

from fastapi import FastAPI

from taskmaster_backend.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="TaskMaster Backend", version="0.1.0")
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
