"""API schemas for Work Item domain endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from taskmaster_backend.work_items.models import WorkItem

WorkItemType = Literal["task", "bug", "story", "incident", "subtask"]


class WorkItemApiErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict[str, str] = Field(default_factory=dict)
    correlation_id: str
    field_errors: dict[str, list[str]] = Field(default_factory=dict)
    retry_after: int | None = None


class WorkItemCreateRequest(BaseModel):
    type: WorkItemType
    status: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=255)
    sprint_id: str | None = Field(default=None, max_length=36)
    epic_id: str | None = Field(default=None, max_length=36)
    assignee_id: str | None = Field(default=None, max_length=36)
    reporter_id: str | None = Field(default=None, max_length=36)
    current_state_id: str | None = Field(default=None, max_length=36)
    description: str | None = None
    priority: str | None = Field(default=None, max_length=64)
    severity: str | None = Field(default=None, max_length=64)
    estimate: int | None = None
    typed_metadata: dict[str, object] = Field(default_factory=dict)


class WorkItemResponse(BaseModel):
    id: str
    project_id: str
    sprint_id: str | None
    epic_id: str | None
    assignee_id: str | None
    reporter_id: str | None
    current_state_id: str | None
    type: str
    status: str
    title: str
    description: str | None
    priority: str | None
    severity: str | None
    estimate: int | None
    typed_metadata: dict[str, object]
    version: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, work_item: WorkItem) -> "WorkItemResponse":
        return cls(
            id=work_item.id,
            project_id=work_item.project_id,
            sprint_id=work_item.sprint_id,
            epic_id=work_item.epic_id,
            assignee_id=work_item.assignee_id,
            reporter_id=work_item.reporter_id,
            current_state_id=work_item.current_state_id,
            type=work_item.type,
            status=work_item.status,
            title=work_item.title,
            description=work_item.description,
            priority=work_item.priority,
            severity=work_item.severity,
            estimate=work_item.estimate,
            typed_metadata=work_item.typed_metadata,
            version=work_item.version,
            created_at=work_item.created_at,
            updated_at=work_item.updated_at,
        )
