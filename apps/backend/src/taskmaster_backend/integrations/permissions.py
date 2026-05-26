"""Stable permission contracts for integration-owned capabilities."""

from __future__ import annotations

from typing import Final

from taskmaster_backend.identity.authorization import PermissionRequirement
from taskmaster_backend.identity.rbac import PermissionScope

INTEGRATION_WEBHOOK_MANAGE_PERMISSION: Final = "integration.webhook.manage"


def webhook_management_requirement(organization_id: str) -> PermissionRequirement:
    """Return the organization-scoped requirement for webhook administration."""
    if organization_id.strip() == "":
        raise ValueError("organization_id is required")

    return PermissionRequirement(
        permission=INTEGRATION_WEBHOOK_MANAGE_PERMISSION,
        scope=PermissionScope(scope_type="organization", scope_id=organization_id),
    )
