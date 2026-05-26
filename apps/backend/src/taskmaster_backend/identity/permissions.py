"""Stable permission contracts for identity-owned capabilities."""

from __future__ import annotations

from typing import Final

from taskmaster_backend.identity.authorization import PermissionRequirement
from taskmaster_backend.identity.rbac import PermissionScope

API_TOKEN_MANAGE_PERMISSION: Final = "api_token.manage"


def api_token_management_requirement(organization_id: str) -> PermissionRequirement:
    """Return the organization-scoped requirement for API token administration."""
    if organization_id.strip() == "":
        raise ValueError("organization_id is required")

    return PermissionRequirement(
        permission=API_TOKEN_MANAGE_PERMISSION,
        scope=PermissionScope(scope_type="organization", scope_id=organization_id),
    )
