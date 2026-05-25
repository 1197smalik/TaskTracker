"""Audit writer service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from taskmaster_backend.audit.models import AuditLog, EventOutbox
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


def create_outbox_event(
    session: Session,
    event_type: str,
    occurred_at: datetime,
    actor_id: str | None,
    organization_id: str,
    workspace_id: str | None,
    project_id: str | None,
    entity_type: str,
    entity_id: str,
    correlation_id: str,
    payload: dict[str, object],
    payload_version: str = "1.0",
) -> EventOutbox:
    """Create an outbox record for a domain event.

    This function records domain events in the outbox table for reliable dispatch.
    Events are recorded in the same transaction as the business state change,
    ensuring consistency.

    Args:
        session: SQLAlchemy session for database operations.
        event_type: The domain event type (e.g., "work_item.created").
        occurred_at: When the event occurred in UTC.
        actor_id: The user who triggered the event (optional).
        organization_id: The organization owning the event.
        workspace_id: The workspace containing the event (optional).
        project_id: The project containing the event (optional).
        entity_type: The type of entity affected (e.g., "work_item").
        entity_id: The ID of the affected entity.
        correlation_id: Request correlation ID for tracing.
        payload: Event payload as a dictionary.
        payload_version: Schema version of the payload (default: "1.0").

    Returns:
        The created EventOutbox record (not yet committed).

    Raises:
        ValueError: If required fields are missing or invalid.
    """
    _require_non_empty(event_type, "event_type")
    _require_non_empty(organization_id, "organization_id")
    _require_non_empty(entity_type, "entity_type")
    _require_non_empty(entity_id, "entity_id")
    _require_non_empty(correlation_id, "correlation_id")

    event = EventOutbox(
        event_id=str(uuid4()),
        event_type=event_type,
        occurred_at=occurred_at,
        actor_id=actor_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        project_id=project_id,
        entity_type=entity_type,
        entity_id=entity_id,
        correlation_id=correlation_id,
        payload=payload,
        payload_version=payload_version,
        status="pending",
        retry_count=0,
    )

    session.add(event)
    return event
