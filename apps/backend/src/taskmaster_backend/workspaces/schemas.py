"""API schemas for workspace creation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class WorkspaceCreateRequest(BaseModel):
    name: str | None = None


class WorkspaceResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    created_at: datetime
    updated_at: datetime


class WorkspaceCreateResponse(BaseModel):
    workspace: WorkspaceResponse
