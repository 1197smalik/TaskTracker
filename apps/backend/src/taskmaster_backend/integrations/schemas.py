"""API schemas for organization-scoped webhook management."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WebhookEndpointCreateRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    description: str | None = Field(default=None, max_length=255)
    workspace_id: str | None = None
    event_types: list[str] = Field(default_factory=list)
    project_filters: list[str] = Field(default_factory=list)


class WebhookEndpointResponse(BaseModel):
    id: str
    organization_id: str
    workspace_id: str | None
    url: str
    description: str | None
    event_types: list[str]
    project_filters: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class WebhookEndpointCreateResponse(BaseModel):
    webhook_endpoint: WebhookEndpointResponse
    secret: str


class WebhookEndpointListResponse(BaseModel):
    items: list[WebhookEndpointResponse]
