"""API schemas for project-domain endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from taskmaster_backend.workflows.models import WorkflowState


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


class ProjectVersionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ProjectVersionResponse(BaseModel):
    id: str
    project_id: str
    name: str
    created_at: datetime
    updated_at: datetime


class ProjectVersionListResponse(BaseModel):
    items: list[ProjectVersionResponse]


class ProjectWorkflowStateResponse(BaseModel):
    id: str
    name: str
    position: int

    @classmethod
    def from_model(cls, workflow_state: WorkflowState) -> "ProjectWorkflowStateResponse":
        return cls(
            id=workflow_state.id,
            name=workflow_state.name,
            position=workflow_state.position,
        )


class ProjectWorkflowStateCatalogResponse(BaseModel):
    workflow_definition_id: str
    states: list[ProjectWorkflowStateResponse]
