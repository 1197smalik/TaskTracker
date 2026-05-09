"""Tests for the refresh token endpoint contract."""

from fastapi.routing import APIRoute

from taskmaster_backend.app import create_app
from taskmaster_backend.identity.routes import refresh_token
from taskmaster_backend.identity.schemas import RefreshTokenRequest


def test_refresh_token_route_is_registered_under_versioned_api() -> None:
    app = create_app()
    route_map = {
        route.path: route
        for route in app.routes
        if isinstance(route, APIRoute)
    }

    assert "/api/v1/auth/refresh" in route_map
    assert "POST" in route_map["/api/v1/auth/refresh"].methods


def test_refresh_token_route_openapi_contract_is_exposed() -> None:
    app = create_app()
    openapi_schema = app.openapi()
    path_item = openapi_schema["paths"]["/api/v1/auth/refresh"]["post"]

    assert path_item["summary"] == "Exchange refresh token"
    assert "requestBody" in path_item
    assert "200" in path_item["responses"]
    assert "501" in path_item["responses"]

    components = openapi_schema["components"]["schemas"]
    assert "RefreshTokenRequest" in components
    assert "RefreshTokenResponse" in components
    assert "ApiErrorResponse" in components
    assert set(components["RefreshTokenRequest"]["required"]) == {"refresh_token"}


def test_refresh_token_route_returns_non_leaky_not_implemented_error() -> None:
    response = refresh_token(RefreshTokenRequest(refresh_token="raw-refresh-token"))

    assert response.status_code == 501
    assert response.body
    assert b"refresh_token_not_implemented" in response.body
    assert b"raw-refresh-token" not in response.body
    assert b"token_hash" not in response.body
