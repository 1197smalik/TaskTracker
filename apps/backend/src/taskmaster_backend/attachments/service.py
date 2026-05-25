"""Application service for attachment upload metadata."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.orm import Session

from taskmaster_backend.attachments.repository import create_attachment_metadata
from taskmaster_backend.attachments.schemas import AttachmentUploadCreateRequest
from taskmaster_backend.attachments.storage import (
    ObjectStorageAdapter,
    ObjectStorageUploadRequest,
    ObjectStorageUploadTarget,
)
from taskmaster_backend.collaboration.models import Attachment


@dataclass(frozen=True, slots=True)
class AttachmentUploadMetadataResult:
    """Metadata and upload target for a newly registered attachment."""

    attachment: Attachment
    upload_target: ObjectStorageUploadTarget


def create_attachment_upload_metadata(
    session: Session,
    *,
    work_item_id: str,
    uploader_id: str,
    request: AttachmentUploadCreateRequest,
    storage_adapter: ObjectStorageAdapter,
) -> AttachmentUploadMetadataResult:
    """Create attachment metadata and a provider-neutral upload target."""
    storage_key = _build_storage_key(work_item_id, request.file_name)
    upload_target = storage_adapter.create_upload_target(
        ObjectStorageUploadRequest(
            storage_key=storage_key,
            content_type=request.content_type,
            size_bytes=request.size_bytes,
        )
    )
    attachment = create_attachment_metadata(
        session,
        work_item_id=work_item_id,
        uploader_id=uploader_id,
        storage_key=storage_key,
        file_name=request.file_name,
        content_type=request.content_type,
        size_bytes=request.size_bytes,
        commit=False,
    )
    session.commit()
    session.refresh(attachment)
    return AttachmentUploadMetadataResult(
        attachment=attachment,
        upload_target=upload_target,
    )


def _build_storage_key(work_item_id: str, file_name: str) -> str:
    return f"attachments/{work_item_id}/{uuid4()}/{file_name}"
