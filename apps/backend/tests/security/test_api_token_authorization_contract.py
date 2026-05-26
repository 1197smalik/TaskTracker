"""Tests for API token management authorization contract."""

from __future__ import annotations

import pytest
from fastapi.routing import APIRoute

from taskmaster_backend.app import create_app
from taskmaster_backend.identity.permissions import (
    API_TOKEN_MANAGE_PERMISSION,
    api_token_management_requirement,
)


def test_api_token_management_permission_code_is_stable() -> None:
    assert API_TOKEN_MANAGE_PERMISSION == "api_token.manage"


def test_api_token_management_requirement_is_organization_scoped() -> None:
    requirement = api_token_management_requirement("org-1")

    assert requirement.permission == API_TOKEN_MANAGE_PERMISSION
    assert requirement.scope.scope_type == "organization"
    assert requirement.scope.scope_id == "org-1"


def test_api_token_management_requirement_rejects_missing_organization() -> None:
    with pytest.raises(ValueError, match="organization_id is required"):
        api_token_management_requirement(" ")


def test_api_token_authorization_contract_does_not_add_endpoint_behavior() -> None:
    app = create_app()
    api_token_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute) and "api-token" in route.path
    ]

    assert api_token_routes == []


def test_api_token_authorization_contract_does_not_add_management_behavior() -> None:
    app = create_app()
    management_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and (
            route.path.endswith("/api-tokens")
            or "/api-tokens/" in route.path
            or route.path.endswith("/tokens")
        )
    ]

    assert management_routes == []
