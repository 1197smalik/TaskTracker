"""Persistence helpers for attachment metadata."""

from __future__ import annotations

from sqlalchemy.orm import Session

from taskmaster_backend.collaboration.models import Attachment


def create_attachment_metadata(
    session: Session,
    *,
    work_item_id: str,
    uploader_id: str,
    storage_key: str,
    file_name: str,
    content_type: str,
    size_bytes: int,
    commit: bool = True,
) -> Attachment:
    attachment = Attachment(
        work_item_id=work_item_id,
        uploader_id=uploader_id,
        storage_key=storage_key,
        file_name=file_name,
        content_type=content_type,
        size_bytes=size_bytes,
    )
    session.add(attachment)
    session.flush()

    if commit:
        session.commit()
        session.refresh(attachment)

    return attachment
