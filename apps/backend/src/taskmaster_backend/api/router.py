"""Top-level API router for versioned backend endpoints."""

from fastapi import APIRouter

from taskmaster_backend.api.health import router as health_router
from taskmaster_backend.collaboration.routes import router as collaboration_router
from taskmaster_backend.identity.routes import router as identity_router
from taskmaster_backend.notifications.routes import router as notifications_router
from taskmaster_backend.projects.routes import router as projects_router
from taskmaster_backend.work_items.routes import router as work_items_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["platform"])
api_router.include_router(identity_router)
api_router.include_router(projects_router)
api_router.include_router(work_items_router)
api_router.include_router(collaboration_router)
api_router.include_router(notifications_router)
