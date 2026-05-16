"""Top-level API router for versioned backend endpoints."""

from fastapi import APIRouter

from taskmaster_backend.api.health import router as health_router
from taskmaster_backend.identity.routes import router as identity_router
from taskmaster_backend.projects.routes import router as projects_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["platform"])
api_router.include_router(identity_router)
api_router.include_router(projects_router)
