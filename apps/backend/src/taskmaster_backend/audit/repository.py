"""Persistence helpers for audit write behavior."""

from __future__ import annotations

from sqlalchemy.orm import Session

from taskmaster_backend.audit.models import AuditLog


def create_audit_log(
    session: Session,
    audit_log: AuditLog,
    *,
    commit: bool = True,
) -> AuditLog:
    session.add(audit_log)
    session.flush()

    if commit:
        session.commit()
        session.refresh(audit_log)

    return audit_log
