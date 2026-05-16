"""Workflow transition validation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from sqlalchemy.orm import Session

from taskmaster_backend.work_items.models import WorkItem
from taskmaster_backend.workflows.models import WorkflowTransitionRule
from taskmaster_backend.workflows.repository import (
    get_project_work_item,
    get_project_workflow_assignment,
    get_workflow_state,
    get_workflow_transition,
    list_child_work_items,
    list_transition_rules,
)

MISSING_WORKFLOW_ASSIGNMENT: Final = "missing_workflow_assignment"
WORK_ITEM_NOT_FOUND: Final = "work_item_not_found"
SOURCE_STATE_MISMATCH: Final = "source_state_mismatch"
WORKFLOW_STATE_MISMATCH: Final = "workflow_state_mismatch"
MISSING_TRANSITION: Final = "missing_transition"
RULE_DENIED: Final = "rule_denied"


@dataclass(frozen=True)
class WorkflowTransitionValidationRequest:
    project_id: str
    work_item_id: str
    target_state_id: str
    source_state_id: str | None = None
    actor_id: str | None = None
    actor_role_ids: frozenset[str] = field(default_factory=frozenset)
    actor_permissions: frozenset[str] = field(default_factory=frozenset)
    comment_provided: bool = False


@dataclass(frozen=True)
class WorkflowTransitionValidationResult:
    allowed: bool
    error_code: str | None = None
    transition_id: str | None = None
    rule_type: str | None = None


def validate_work_item_transition(
    session: Session,
    request: WorkflowTransitionValidationRequest,
) -> WorkflowTransitionValidationResult:
    assignment = get_project_workflow_assignment(session, request.project_id)
    if assignment is None:
        return WorkflowTransitionValidationResult(
            allowed=False,
            error_code=MISSING_WORKFLOW_ASSIGNMENT,
        )

    work_item = get_project_work_item(
        session,
        request.project_id,
        request.work_item_id,
    )
    if work_item is None:
        return WorkflowTransitionValidationResult(
            allowed=False,
            error_code=WORK_ITEM_NOT_FOUND,
        )

    if request.source_state_id is not None and (
        request.source_state_id != work_item.current_state_id
    ):
        return WorkflowTransitionValidationResult(
            allowed=False,
            error_code=SOURCE_STATE_MISMATCH,
        )

    if work_item.current_state_id is None:
        return WorkflowTransitionValidationResult(
            allowed=False,
            error_code=SOURCE_STATE_MISMATCH,
        )

    source_state = get_workflow_state(
        session,
        assignment.workflow_definition_id,
        work_item.current_state_id,
    )
    if source_state is None:
        return WorkflowTransitionValidationResult(
            allowed=False,
            error_code=WORKFLOW_STATE_MISMATCH,
        )

    transition = get_workflow_transition(
        session,
        assignment.workflow_definition_id,
        work_item.current_state_id,
        request.target_state_id,
    )
    if transition is None:
        return WorkflowTransitionValidationResult(
            allowed=False,
            error_code=MISSING_TRANSITION,
        )

    for rule in list_transition_rules(session, transition.id):
        if not _rule_allows_transition(session, request, work_item, rule):
            return WorkflowTransitionValidationResult(
                allowed=False,
                error_code=RULE_DENIED,
                transition_id=transition.id,
                rule_type=rule.rule_type,
            )

    return WorkflowTransitionValidationResult(
        allowed=True,
        transition_id=transition.id,
    )


def _rule_allows_transition(
    session: Session,
    request: WorkflowTransitionValidationRequest,
    work_item: WorkItem,
    rule: WorkflowTransitionRule,
) -> bool:
    if rule.rule_type == "required_fields":
        return _required_fields_present(work_item, rule.config)
    if rule.rule_type == "allowed_roles":
        return _actor_has_allowed_role_or_permission(request, rule.config)
    if rule.rule_type == "assignee_reporter":
        return _actor_matches_assignee_reporter_constraint(request, work_item, rule.config)
    if rule.rule_type == "parent_child_completion":
        return _children_satisfy_completion_rule(
            session,
            request.project_id,
            work_item,
            rule.config,
        )
    if rule.rule_type == "comment_required":
        return not bool(rule.config.get("required", True)) or request.comment_provided
    return False


def _required_fields_present(
    work_item: WorkItem,
    config: dict[str, object],
) -> bool:
    field_names = _string_list(config.get("fields"))
    return all(_work_item_value_present(work_item, field_name) for field_name in field_names)


def _actor_has_allowed_role_or_permission(
    request: WorkflowTransitionValidationRequest,
    config: dict[str, object],
) -> bool:
    allowed_roles = set(_string_list(config.get("roles")))
    allowed_permissions = set(_string_list(config.get("permissions")))
    if not allowed_roles and not allowed_permissions:
        return True

    return bool(
        allowed_roles.intersection(request.actor_role_ids)
        or allowed_permissions.intersection(request.actor_permissions)
    )


def _actor_matches_assignee_reporter_constraint(
    request: WorkflowTransitionValidationRequest,
    work_item: WorkItem,
    config: dict[str, object],
) -> bool:
    required_actor = config.get("required_actor")
    if required_actor == "assignee":
        return request.actor_id is not None and request.actor_id == work_item.assignee_id
    if required_actor == "reporter":
        return request.actor_id is not None and request.actor_id == work_item.reporter_id
    return True


def _children_satisfy_completion_rule(
    session: Session,
    project_id: str,
    work_item: WorkItem,
    config: dict[str, object],
) -> bool:
    completed_state_ids = set(_string_list(config.get("completed_state_ids")))
    completed_statuses = set(_string_list(config.get("completed_statuses")))
    if not completed_state_ids and not completed_statuses:
        return True

    children = list_child_work_items(session, project_id, work_item.id)
    return all(
        (not completed_state_ids or child.current_state_id in completed_state_ids)
        and (not completed_statuses or child.status in completed_statuses)
        for child in children
    )


def _work_item_value_present(work_item: WorkItem, field_name: str) -> bool:
    if hasattr(work_item, field_name):
        value = getattr(work_item, field_name)
    else:
        value = work_item.typed_metadata.get(field_name)

    return value is not None and value != "" and value != []


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    return [item for item in value if isinstance(item, str)]
