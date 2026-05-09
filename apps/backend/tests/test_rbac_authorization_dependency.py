"""Tests for scoped RBAC authorization dependency behavior."""

from __future__ import annotations

from typing import Any, cast

import pytest
from fastapi import HTTPException

from taskmaster_backend.identity.authorization import (
    PermissionRequirement,
    authorize_principal,
    require_scoped_permission,
)
from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal, get_current_principal
from taskmaster_backend.identity.rbac import PermissionGrant, PermissionScope


def test_rbac_dependency_allows_matching_permission_and_scope() -> None:
    requirement = PermissionRequirement(
        permission="project.update",
        scope=PermissionScope(scope_type="project", scope_id="project-1"),
    )
    grants = [
        PermissionGrant(
            actor_id="user-123",
            permission="project.update",
            scope=PermissionScope(scope_type="project", scope_id="project-1"),
        ),
    ]
    dependency = require_scoped_permission(requirement, grant_provider=lambda: grants)

    principal = dependency(_principal(), grants)

    assert principal.subject == "user-123"


def test_rbac_dependency_denies_missing_token_before_authorization() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_current_principal(None)

    assert exc_info.value.status_code == 401
    assert _error_detail(exc_info.value)["error_code"] == "missing_bearer_token"


def test_rbac_dependency_denies_scope_mismatch() -> None:
    requirement = PermissionRequirement(
        permission="project.update",
        scope=PermissionScope(scope_type="project", scope_id="project-2"),
    )
    grants = [
        PermissionGrant(
            actor_id="user-123",
            permission="project.update",
            scope=PermissionScope(scope_type="project", scope_id="project-1"),
        ),
    ]

    with pytest.raises(HTTPException) as exc_info:
        authorize_principal(_principal(), requirement, grants)

    assert exc_info.value.status_code == 403
    assert _error_detail(exc_info.value)["error_code"] == "permission_denied"
    assert _error_detail(exc_info.value)["reason"] == "scope_mismatch"


def test_rbac_dependency_denies_missing_permission() -> None:
    requirement = PermissionRequirement(
        permission="project.delete",
        scope=PermissionScope(scope_type="project", scope_id="project-1"),
    )
    grants = [
        PermissionGrant(
            actor_id="user-123",
            permission="project.update",
            scope=PermissionScope(scope_type="project", scope_id="project-1"),
        ),
    ]

    with pytest.raises(HTTPException) as exc_info:
        authorize_principal(_principal(), requirement, grants)

    assert exc_info.value.status_code == 403
    assert _error_detail(exc_info.value)["error_code"] == "permission_denied"
    assert _error_detail(exc_info.value)["reason"] == "missing_permission"


def test_rbac_dependency_denies_by_default_without_grants() -> None:
    requirement = PermissionRequirement(
        permission="project.update",
        scope=PermissionScope(scope_type="project", scope_id="project-1"),
    )

    with pytest.raises(HTTPException) as exc_info:
        authorize_principal(_principal(), requirement, grants=[])

    assert exc_info.value.status_code == 403
    assert _error_detail(exc_info.value)["reason"] == "missing_permission"


def _principal() -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        subject="user-123",
        issuer="test-issuer",
        audience="test-audience",
        expires_at=9_999_999_999,
    )


def _error_detail(exc: HTTPException) -> dict[str, Any]:
    return cast(dict[str, Any], exc.detail)
