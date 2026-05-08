"""Smoke tests for backend project discovery and health boundary."""

from fastapi.routing import APIRoute

from taskmaster_backend import __version__
from taskmaster_backend.app import create_app


def test_package_version_is_defined() -> None:
    assert __version__ == "0.1.0"


def test_app_factory_returns_fastapi_app() -> None:
    app = create_app()
    assert app.title == "TaskMaster Backend"


def test_health_route_is_registered() -> None:
    app = create_app()
    route_paths = {
        route.path
        for route in app.routes
        if isinstance(route, APIRoute)
    }
    assert "/api/v1/health" in route_paths
