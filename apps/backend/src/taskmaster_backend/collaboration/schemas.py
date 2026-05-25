"""API schemas for Collaboration domain endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from taskmaster_backend.collaboration.models import Comment


class CommentApiErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict[str, str] = Field(default_factory=dict)
    correlation_id: str
    field_errors: dict[str, list[str]] = Field(default_factory=dict)
    retry_after: int | None = None


class CommentCreateRequest(BaseModel):
    body: str = Field(min_length=1)

    @field_validator("body")
    @classmethod
    def reject_blank_body(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Comment body must not be blank.")
        return value


class CommentResponse(BaseModel):
    id: str
    work_item_id: str
    author_id: str
    body: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, comment: Comment) -> "CommentResponse":
        return cls(
            id=comment.id,
            work_item_id=comment.work_item_id,
            author_id=comment.author_id,
            body=comment.body,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )
