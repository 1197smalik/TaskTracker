"""API schemas for organization creation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class OrganizationCreateRequest(BaseModel):
    name: str | None = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime


class OrganizationCreateResponse(BaseModel):
    organization: OrganizationResponse
