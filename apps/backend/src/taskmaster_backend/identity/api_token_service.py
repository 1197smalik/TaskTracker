"""Application service for API token management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from taskmaster_backend.identity.api_token_repository import (
    create_api_token_record,
    get_api_token_for_organization,
    list_api_tokens_for_organization,
    organization_exists,
)
from taskmaster_backend.identity.api_token_schemas import ApiTokenCreateRequest
from taskmaster_backend.identity.api_tokens import generate_api_token, hash_api_token
from taskmaster_backend.identity.models import ApiToken


@dataclass(frozen=True, slots=True)
class ApiTokenCreateResult:
    api_token: ApiToken
    token: str


def create_organization_api_token(
    session: Session,
    *,
    organization_id: str,
    request: ApiTokenCreateRequest,
) -> ApiTokenCreateResult | None:
    """Create API token metadata and return raw token material exactly once."""
    if not organization_exists(session, organization_id):
        return None

    token = generate_api_token()
    api_token = create_api_token_record(
        session,
        organization_id=organization_id,
        name=request.name,
        token_hash=hash_api_token(token),
        scopes=list(request.scopes),
        expires_at=request.expires_at,
    )
    return ApiTokenCreateResult(api_token=api_token, token=token)


def list_organization_api_tokens(
    session: Session,
    *,
    organization_id: str,
) -> list[ApiToken] | None:
    if not organization_exists(session, organization_id):
        return None
    return list_api_tokens_for_organization(session, organization_id=organization_id)


def revoke_organization_api_token(
    session: Session,
    *,
    organization_id: str,
    api_token_id: str,
) -> ApiToken | None:
    if not organization_exists(session, organization_id):
        return None

    api_token = get_api_token_for_organization(
        session,
        organization_id=organization_id,
        api_token_id=api_token_id,
    )
    if api_token is None:
        return None
    if api_token.revoked_at is None:
        api_token.revoked_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(api_token)
    return api_token
