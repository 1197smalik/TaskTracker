"""API schemas for attachment endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from taskmaster_backend.attachments.storage import ObjectStorageUploadTarget
from taskmaster_backend.collaboration.models import Attachment


class AttachmentApiErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict[str, str] = Field(default_factory=dict)
    correlation_id: str
    field_errors: dict[str, list[str]] = Field(default_factory=dict)
    retry_after: int | None = None


class AttachmentUploadCreateRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(ge=0)

    @field_validator("file_name", "content_type")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be blank.")
        return value


class AttachmentResponse(BaseModel):
    id: str
    work_item_id: str
    uploader_id: str
    storage_key: str
    file_name: str
    content_type: str
    size_bytes: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, attachment: Attachment) -> "AttachmentResponse":
        return cls(
            id=attachment.id,
            work_item_id=attachment.work_item_id,
            uploader_id=attachment.uploader_id,
            storage_key=attachment.storage_key,
            file_name=attachment.file_name,
            content_type=attachment.content_type,
            size_bytes=attachment.size_bytes,
            created_at=attachment.created_at,
            updated_at=attachment.updated_at,
        )


class AttachmentUploadTargetResponse(BaseModel):
    upload_url: str
    method: str
    headers: dict[str, str]
    expires_at: datetime

    @classmethod
    def from_target(
        cls,
        target: ObjectStorageUploadTarget,
    ) -> "AttachmentUploadTargetResponse":
        return cls(
            upload_url=target.upload_url,
            method=target.method,
            headers=target.headers,
            expires_at=target.expires_at,
        )


class AttachmentUploadCreateResponse(BaseModel):
    attachment: AttachmentResponse
    upload: AttachmentUploadTargetResponse
