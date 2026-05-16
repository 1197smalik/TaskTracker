"""API schemas for project-domain endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectApiErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict[str, str] = Field(default_factory=dict)
    correlation_id: str
    field_errors: dict[str, list[str]] = Field(default_factory=dict)
    retry_after: int | None = None


class ProjectLabelCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ProjectLabelResponse(BaseModel):
    id: str
    project_id: str
    name: str
    created_at: datetime
    updated_at: datetime


class ProjectLabelListResponse(BaseModel):
    items: list[ProjectLabelResponse]


class ProjectComponentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ProjectComponentResponse(BaseModel):
    id: str
    project_id: str
    name: str
    created_at: datetime
    updated_at: datetime


class ProjectComponentListResponse(BaseModel):
    items: list[ProjectComponentResponse]
