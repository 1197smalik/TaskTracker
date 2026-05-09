"""FastAPI RBAC authorization dependencies for scoped endpoints."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status

from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal, get_current_principal
from taskmaster_backend.identity.rbac import (
    PermissionEvaluationRequest,
    PermissionGrant,
    PermissionScope,
    evaluate_permission,
)

GrantProvider = Callable[[], Iterable[PermissionGrant]]


@dataclass(frozen=True)
class PermissionRequirement:
    permission: str
    scope: PermissionScope


def empty_permission_grants() -> tuple[PermissionGrant, ...]:
    """Default placeholder until database-backed grant loading exists."""

    return ()


def authorize_principal(
    principal: AuthenticatedPrincipal,
    requirement: PermissionRequirement,
    grants: Iterable[PermissionGrant],
) -> AuthenticatedPrincipal:
    decision = evaluate_permission(
        PermissionEvaluationRequest(
            actor_id=principal.subject,
            permission=requirement.permission,
            scope=requirement.scope,
        ),
        grants=grants,
    )
    if decision.allowed:
        return principal

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error_code": "permission_denied",
            "message": "Permission denied.",
            "reason": decision.denial_reason,
            "audit_marker": decision.audit_marker,
        },
    )


def require_scoped_permission(
    requirement: PermissionRequirement,
    grant_provider: GrantProvider = empty_permission_grants,
) -> Callable[[AuthenticatedPrincipal, Iterable[PermissionGrant]], AuthenticatedPrincipal]:
    def dependency(
        principal: Annotated[AuthenticatedPrincipal, Depends(get_current_principal)],
        grants: Annotated[Iterable[PermissionGrant], Depends(grant_provider)],
    ) -> AuthenticatedPrincipal:
        return authorize_principal(principal, requirement, grants)

    return dependency
