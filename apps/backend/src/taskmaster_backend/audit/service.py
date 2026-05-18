"""Audit writer service."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from taskmaster_backend.audit.models import AuditLog
from taskmaster_backend.audit.repository import create_audit_log


@dataclass(frozen=True)
class AuditLogWriteRequest:
    actor_type: str
    organization_id: str
    entity_type: str
    entity_id: str
    action: str
    correlation_id: str
    actor_id: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    before_summary: dict[str, object] | None = None
    after_summary: dict[str, object] | None = None
    diff_reference: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None


def write_audit_log(
    session: Session,
    request: AuditLogWriteRequest,
    *,
    commit: bool = True,
) -> AuditLog:
    _require_non_empty(request.actor_type, "actor_type")
    _require_non_empty(request.organization_id, "organization_id")
    _require_non_empty(request.entity_type, "entity_type")
    _require_non_empty(request.entity_id, "entity_id")
    _require_non_empty(request.action, "action")
    _require_non_empty(request.correlation_id, "correlation_id")

    audit_log = AuditLog(
        actor_id=request.actor_id,
        actor_type=request.actor_type,
        organization_id=request.organization_id,
        workspace_id=request.workspace_id,
        project_id=request.project_id,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        action=request.action,
        before_summary=request.before_summary,
        after_summary=request.after_summary,
        diff_reference=request.diff_reference,
        ip_address=request.ip_address,
        user_agent=request.user_agent,
        correlation_id=request.correlation_id,
    )
    return create_audit_log(session, audit_log, commit=commit)


def _require_non_empty(value: str, field_name: str) -> None:
    if value.strip() == "":
        raise ValueError(f"{field_name} is required")
