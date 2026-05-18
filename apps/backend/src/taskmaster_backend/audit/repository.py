"""Persistence helpers for audit write behavior."""

from __future__ import annotations

from sqlalchemy.orm import Session

from taskmaster_backend.audit.models import AuditLog


def create_audit_log(session: Session, audit_log: AuditLog) -> AuditLog:
    session.add(audit_log)
    session.commit()
    session.refresh(audit_log)
    return audit_log
