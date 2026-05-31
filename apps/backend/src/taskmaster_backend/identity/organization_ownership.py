"""Minimal organization ownership persistence helpers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskmaster_backend.identity.models import Organization, User


def backfill_organization_owners(session: Session) -> int:
    """Assign a deterministic owner to legacy organizations missing ownership."""
    session.flush()

    owner_user_id = session.scalar(
        select(User.id)
        .where(User.is_active.is_(True))
        .order_by(User.created_at.asc(), User.id.asc())
        .limit(1)
    )
    if owner_user_id is None:
        return 0

    organizations = session.scalars(
        select(Organization)
        .where(Organization.owner_user_id.is_(None))
        .order_by(Organization.created_at.asc(), Organization.id.asc())
    ).all()

    for organization in organizations:
        organization.owner_user_id = owner_user_id

    session.flush()
    return len(organizations)
