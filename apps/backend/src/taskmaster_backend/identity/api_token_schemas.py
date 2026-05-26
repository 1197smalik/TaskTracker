"""API schemas for organization-scoped API token management."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ApiTokenCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    scopes: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None


class ApiTokenResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    scopes: list[str]
    expires_at: datetime | None
    revoked_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ApiTokenCreateResponse(BaseModel):
    api_token: ApiTokenResponse
    token: str


class ApiTokenListResponse(BaseModel):
    items: list[ApiTokenResponse]
