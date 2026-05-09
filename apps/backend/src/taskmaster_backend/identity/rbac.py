"""Pure RBAC permission evaluator for backend-owned authorization decisions."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

ScopeType = Literal["organization", "workspace", "project"]


@dataclass(frozen=True)
class PermissionScope:
    scope_type: ScopeType
    scope_id: str


@dataclass(frozen=True)
class PermissionGrant:
    actor_id: str
    permission: str
    scope: PermissionScope


@dataclass(frozen=True)
class PermissionEvaluationRequest:
    actor_id: str
    permission: str
    scope: PermissionScope


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    denial_reason: str | None
    audit_marker: str | None


def evaluate_permission(
    request: PermissionEvaluationRequest,
    grants: Iterable[PermissionGrant],
) -> PermissionDecision:
    """Evaluate one backend-resolved permission request against scoped grants."""

    if request.actor_id == "":
        return _deny("missing_actor", audit_marker="rbac.denied.missing_actor")
    if request.permission == "":
        return _deny("missing_permission", audit_marker="rbac.denied.missing_permission")
    if request.scope.scope_id == "":
        return _deny("missing_scope", audit_marker="rbac.denied.missing_scope")

    has_permission_in_different_scope = False
    for grant in grants:
        if grant.actor_id != request.actor_id:
            continue
        if grant.permission != request.permission:
            continue
        if grant.scope == request.scope:
            return PermissionDecision(
                allowed=True,
                denial_reason=None,
                audit_marker=None,
            )
        has_permission_in_different_scope = True

    if has_permission_in_different_scope:
        return _deny("scope_mismatch", audit_marker="rbac.denied.scope_mismatch")
    return _deny("missing_permission", audit_marker="rbac.denied.missing_permission")


def _deny(reason: str, *, audit_marker: str) -> PermissionDecision:
    return PermissionDecision(
        allowed=False,
        denial_reason=reason,
        audit_marker=audit_marker,
    )
