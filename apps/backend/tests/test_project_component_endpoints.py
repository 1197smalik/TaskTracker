"""Tests for project component endpoint contracts."""

from fastapi.routing import APIRoute

from taskmaster_backend.app import create_app
from taskmaster_backend.projects.routes import (
    create_project_component,
    list_project_components,
)
from taskmaster_backend.projects.schemas import ProjectComponentCreateRequest


def test_project_component_routes_are_registered_under_versioned_api() -> None:
    app = create_app()
    routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path == "/api/v1/projects/{project_id}/components"
    ]

    assert len(routes) == 2
    methods = {method for route in routes for method in route.methods}
    assert methods == {"GET", "POST"}


def test_project_component_routes_openapi_contract_is_exposed() -> None:
    app = create_app()
    openapi_schema = app.openapi()
    get_path_item = openapi_schema["paths"]["/api/v1/projects/{project_id}/components"]["get"]
    post_path_item = openapi_schema["paths"]["/api/v1/projects/{project_id}/components"]["post"]

    assert get_path_item["summary"] == "List project components"
    assert "200" in get_path_item["responses"]
    assert "501" in get_path_item["responses"]

    assert post_path_item["summary"] == "Create project component"
    assert "requestBody" in post_path_item
    assert "200" in post_path_item["responses"]
    assert "501" in post_path_item["responses"]

    components = openapi_schema["components"]["schemas"]
    assert "ProjectComponentCreateRequest" in components
    assert "ProjectComponentResponse" in components
    assert "ProjectComponentListResponse" in components
    assert "ProjectApiErrorResponse" in components
    assert set(components["ProjectComponentCreateRequest"]["required"]) == {"name"}


def test_project_component_list_route_returns_non_leaky_not_implemented_error() -> None:
    response = list_project_components("project-123")

    assert response.status_code == 501
    assert response.body
    assert b"project_components_not_implemented" in response.body
    assert b"project-123" not in response.body


def test_project_component_create_route_returns_non_leaky_not_implemented_error() -> None:
    response = create_project_component(
        "project-123",
        ProjectComponentCreateRequest(name="API"),
    )

    assert response.status_code == 501
    assert response.body
    assert b"project_components_not_implemented" in response.body
    assert b"project-123" not in response.body
    assert b"API" not in response.body
