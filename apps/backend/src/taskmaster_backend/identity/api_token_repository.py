"""Persistence helpers for API token management."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskmaster_backend.identity.models import ApiToken, Organization


def organization_exists(session: Session, organization_id: str) -> bool:
    return session.get(Organization, organization_id) is not None


def create_api_token_record(
    session: Session,
    *,
    organization_id: str,
    name: str,
    token_hash: str,
    scopes: list[str],
    expires_at: datetime | None,
    commit: bool = True,
) -> ApiToken:
    api_token = ApiToken(
        organization_id=organization_id,
        name=name,
        token_hash=token_hash,
        scopes=list(scopes),
        expires_at=expires_at,
    )
    session.add(api_token)
    session.flush()

    if commit:
        session.commit()
        session.refresh(api_token)

    return api_token


def list_api_tokens_for_organization(
    session: Session,
    *,
    organization_id: str,
) -> list[ApiToken]:
    return list(
        session.scalars(
            select(ApiToken)
            .where(ApiToken.organization_id == organization_id)
            .order_by(ApiToken.created_at.desc(), ApiToken.id.desc())
        )
    )


def get_api_token_for_organization(
    session: Session,
    *,
    organization_id: str,
    api_token_id: str,
) -> ApiToken | None:
    return session.scalars(
        select(ApiToken).where(
            ApiToken.id == api_token_id,
            ApiToken.organization_id == organization_id,
        )
    ).first()
