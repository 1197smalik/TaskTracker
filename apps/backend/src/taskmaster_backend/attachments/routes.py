"""Attachment API routes."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from taskmaster_backend.attachments.schemas import (
    AttachmentApiErrorResponse,
    AttachmentResponse,
    AttachmentUploadCreateRequest,
    AttachmentUploadCreateResponse,
    AttachmentUploadTargetResponse,
)
from taskmaster_backend.attachments.service import create_attachment_upload_metadata
from taskmaster_backend.attachments.storage import ObjectStorageAdapter
from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal, get_current_principal
from taskmaster_backend.work_items.repository import get_project_work_item

router = APIRouter(
    prefix="/projects/{project_id}/work-items/{work_item_id}/attachments",
    tags=["attachments"],
)


def get_object_storage_adapter() -> ObjectStorageAdapter:
    """Placeholder dependency until a concrete storage adapter is configured."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error_code": "object_storage_not_configured",
            "message": "Object storage adapter is not configured.",
        },
    )


def _work_item_not_found_error() -> AttachmentApiErrorResponse:
    return AttachmentApiErrorResponse(
        error_code="work_item_not_found",
        message="Work item was not found or is inaccessible.",
        correlation_id=str(uuid4()),
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentUploadCreateResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": AttachmentApiErrorResponse,
            "description": "Bearer authentication is required.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": AttachmentApiErrorResponse,
            "description": "Work item was not found or is inaccessible.",
        },
        status.HTTP_501_NOT_IMPLEMENTED: {
            "description": "Object storage adapter is not configured.",
        },
    },
    summary="Create attachment upload metadata",
    description=(
        "Create metadata for a work item attachment and return a provider-neutral "
        "upload target. Concrete storage providers, malware scanning, download URLs, "
        "and attachment list/read APIs are handled by later stories."
    ),
)
def create_attachment_upload(
    project_id: str,
    work_item_id: str,
    request: AttachmentUploadCreateRequest,
    session: Session = Depends(get_db_session),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
    storage_adapter: ObjectStorageAdapter = Depends(get_object_storage_adapter),
) -> AttachmentUploadCreateResponse | JSONResponse:
    work_item = get_project_work_item(session, project_id, work_item_id)
    if work_item is None:
        error = _work_item_not_found_error()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )

    try:
        result = create_attachment_upload_metadata(
            session,
            work_item_id=work_item.id,
            uploader_id=principal.subject,
            request=request,
            storage_adapter=storage_adapter,
        )
    except Exception:
        session.rollback()
        raise

    return AttachmentUploadCreateResponse(
        attachment=AttachmentResponse.from_model(result.attachment),
        upload=AttachmentUploadTargetResponse.from_target(result.upload_target),
    )
