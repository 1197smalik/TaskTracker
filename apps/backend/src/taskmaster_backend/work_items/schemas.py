"""API schemas for Work Item domain endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    parent_id: str | None = Field(default=None, max_length=36)
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


class WorkItemListParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class WorkItemUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)
    type: WorkItemType | None = None
    status: str | None = Field(default=None, min_length=1, max_length=64)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    parent_id: str | None = Field(default=None, max_length=36)
    sprint_id: str | None = Field(default=None, max_length=36)
    epic_id: str | None = Field(default=None, max_length=36)
    assignee_id: str | None = Field(default=None, max_length=36)
    reporter_id: str | None = Field(default=None, max_length=36)
    description: str | None = None
    priority: str | None = Field(default=None, max_length=64)
    severity: str | None = Field(default=None, max_length=64)
    estimate: int | None = None
    typed_metadata: dict[str, object] | None = None

    def update_fields(self) -> dict[str, object | None]:
        data = self.model_dump(exclude_unset=True)
        data.pop("expected_version")
        return data

    @model_validator(mode="after")
    def require_update_field(self) -> Self:
        if not self.update_fields():
            raise ValueError("At least one update field is required.")
        return self


class WorkflowTransitionRequest(BaseModel):
    expected_version: int = Field(ge=1)
    target_state_id: str = Field(min_length=1, max_length=36)
    source_state_id: str | None = Field(default=None, max_length=36)


class WorkItemResponse(BaseModel):
    id: str
    project_id: str
    parent_id: str | None
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
            parent_id=work_item.parent_id,
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


class WorkItemListResponse(BaseModel):
    items: list[WorkItemResponse]
    total: int
    limit: int
    offset: int


class WorkflowTransitionResponse(BaseModel):
    work_item: WorkItemResponse
    transition_id: str
    source_state_id: str
    target_state_id: str
