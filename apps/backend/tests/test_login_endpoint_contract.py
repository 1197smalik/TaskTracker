"""Tests for the login endpoint contract."""

from fastapi.routing import APIRoute

from taskmaster_backend.app import create_app
from taskmaster_backend.identity.routes import login
from taskmaster_backend.identity.schemas import LoginRequest


def test_login_route_is_registered_under_versioned_api() -> None:
    app = create_app()
    route_map = {
        route.path: route
        for route in app.routes
        if isinstance(route, APIRoute)
    }

    assert "/api/v1/auth/login" in route_map
    assert "POST" in route_map["/api/v1/auth/login"].methods


def test_login_route_openapi_contract_is_exposed() -> None:
    app = create_app()
    openapi_schema = app.openapi()
    path_item = openapi_schema["paths"]["/api/v1/auth/login"]["post"]

    assert path_item["summary"] == "Login with email and password"
    assert "requestBody" in path_item
    assert "200" in path_item["responses"]
    assert "501" in path_item["responses"]

    components = openapi_schema["components"]["schemas"]
    assert "LoginRequest" in components
    assert "LoginResponse" in components
    assert "ApiErrorResponse" in components
    assert set(components["LoginRequest"]["required"]) == {"email", "password"}


def test_login_route_returns_non_leaky_not_implemented_error() -> None:
    response = login(LoginRequest(email="person@example.com", password="secret"))

    assert response.status_code == 501
    assert response.body
    assert b"authentication_not_implemented" in response.body
    assert b"person@example.com" not in response.body
    assert b"secret" not in response.body

