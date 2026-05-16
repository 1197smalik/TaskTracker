"""Tests for project version endpoint contracts."""

from fastapi.routing import APIRoute

from taskmaster_backend.app import create_app
from taskmaster_backend.projects.routes import (
    create_project_version,
    list_project_versions,
)
from taskmaster_backend.projects.schemas import ProjectVersionCreateRequest


def test_project_version_routes_are_registered_under_versioned_api() -> None:
    app = create_app()
    routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path == "/api/v1/projects/{project_id}/versions"
    ]

    assert len(routes) == 2
    methods = {method for route in routes for method in route.methods}
    assert methods == {"GET", "POST"}


def test_project_version_routes_openapi_contract_is_exposed() -> None:
    app = create_app()
    openapi_schema = app.openapi()
    get_path_item = openapi_schema["paths"]["/api/v1/projects/{project_id}/versions"]["get"]
    post_path_item = openapi_schema["paths"]["/api/v1/projects/{project_id}/versions"]["post"]

    assert get_path_item["summary"] == "List project versions"
    assert "200" in get_path_item["responses"]
    assert "501" in get_path_item["responses"]

    assert post_path_item["summary"] == "Create project version"
    assert "requestBody" in post_path_item
    assert "200" in post_path_item["responses"]
    assert "501" in post_path_item["responses"]

    components = openapi_schema["components"]["schemas"]
    assert "ProjectVersionCreateRequest" in components
    assert "ProjectVersionResponse" in components
    assert "ProjectVersionListResponse" in components
    assert "ProjectApiErrorResponse" in components
    assert set(components["ProjectVersionCreateRequest"]["required"]) == {"name"}


def test_project_version_list_route_returns_non_leaky_not_implemented_error() -> None:
    response = list_project_versions("project-123")

    assert response.status_code == 501
    assert response.body
    assert b"project_versions_not_implemented" in response.body
    assert b"project-123" not in response.body


def test_project_version_create_route_returns_non_leaky_not_implemented_error() -> None:
    response = create_project_version(
        "project-123",
        ProjectVersionCreateRequest(name="v1.0"),
    )

    assert response.status_code == 501
    assert response.body
    assert b"project_versions_not_implemented" in response.body
    assert b"project-123" not in response.body
    assert b"v1.0" not in response.body
