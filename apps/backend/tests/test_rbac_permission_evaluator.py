"""Tests for the pure RBAC permission evaluator."""

from taskmaster_backend.identity.rbac import (
    PermissionEvaluationRequest,
    PermissionGrant,
    PermissionScope,
    evaluate_permission,
)


def test_evaluate_permission_allows_exact_permission_and_scope_match() -> None:
    decision = evaluate_permission(
        PermissionEvaluationRequest(
            actor_id="user-123",
            permission="project.update",
            scope=PermissionScope(scope_type="project", scope_id="project-1"),
        ),
        grants=[
            PermissionGrant(
                actor_id="user-123",
                permission="project.update",
                scope=PermissionScope(scope_type="project", scope_id="project-1"),
            ),
        ],
    )

    assert decision.allowed is True
    assert decision.denial_reason is None
    assert decision.audit_marker is None


def test_evaluate_permission_denies_by_default_with_no_grants() -> None:
    decision = evaluate_permission(
        PermissionEvaluationRequest(
            actor_id="user-123",
            permission="project.update",
            scope=PermissionScope(scope_type="project", scope_id="project-1"),
        ),
        grants=[],
    )

    assert decision.allowed is False
    assert decision.denial_reason == "missing_permission"
    assert decision.audit_marker == "rbac.denied.missing_permission"


def test_evaluate_permission_denies_missing_permission() -> None:
    decision = evaluate_permission(
        PermissionEvaluationRequest(
            actor_id="user-123",
            permission="project.delete",
            scope=PermissionScope(scope_type="project", scope_id="project-1"),
        ),
        grants=[
            PermissionGrant(
                actor_id="user-123",
                permission="project.update",
                scope=PermissionScope(scope_type="project", scope_id="project-1"),
            ),
        ],
    )

    assert decision.allowed is False
    assert decision.denial_reason == "missing_permission"


def test_evaluate_permission_denies_scope_mismatch() -> None:
    decision = evaluate_permission(
        PermissionEvaluationRequest(
            actor_id="user-123",
            permission="project.update",
            scope=PermissionScope(scope_type="project", scope_id="project-2"),
        ),
        grants=[
            PermissionGrant(
                actor_id="user-123",
                permission="project.update",
                scope=PermissionScope(scope_type="project", scope_id="project-1"),
            ),
        ],
    )

    assert decision.allowed is False
    assert decision.denial_reason == "scope_mismatch"
    assert decision.audit_marker == "rbac.denied.scope_mismatch"


def test_evaluate_permission_ignores_frontend_style_role_labels() -> None:
    decision = evaluate_permission(
        PermissionEvaluationRequest(
            actor_id="user-123",
            permission="Organization Owner",
            scope=PermissionScope(scope_type="organization", scope_id="org-1"),
        ),
        grants=[],
    )

    assert decision.allowed is False
    assert decision.denial_reason == "missing_permission"
