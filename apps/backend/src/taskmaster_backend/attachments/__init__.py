"""Attachment storage contracts."""

from taskmaster_backend.attachments.routes import router
from taskmaster_backend.attachments.storage import (
    ObjectStorageAdapter,
    ObjectStorageUploadRequest,
    ObjectStorageUploadTarget,
)

__all__ = [
    "ObjectStorageAdapter",
    "ObjectStorageUploadRequest",
    "ObjectStorageUploadTarget",
    "router",
]
