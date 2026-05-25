"""Object storage adapter contract for attachments."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ObjectStorageUploadRequest:
    """Request for creating an attachment upload target."""

    storage_key: str
    content_type: str
    size_bytes: int
    expires_in_seconds: int = 900

    def __post_init__(self) -> None:
        if not self.storage_key.strip():
            raise ValueError("storage_key is required")
        if not self.content_type.strip():
            raise ValueError("content_type is required")
        if self.size_bytes < 0:
            raise ValueError("size_bytes cannot be negative")
        if self.expires_in_seconds < 1:
            raise ValueError("expires_in_seconds must be positive")


@dataclass(frozen=True, slots=True)
class ObjectStorageUploadTarget:
    """Provider-neutral upload target returned by an object storage adapter."""

    upload_url: str
    storage_key: str
    expires_at: datetime
    method: str = "PUT"
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.upload_url.strip():
            raise ValueError("upload_url is required")
        if not self.storage_key.strip():
            raise ValueError("storage_key is required")
        if not self.method.strip():
            raise ValueError("method is required")


class ObjectStorageAdapter(Protocol):
    """Contract implemented by concrete object storage providers."""

    def create_upload_target(
        self,
        request: ObjectStorageUploadRequest,
    ) -> ObjectStorageUploadTarget:
        """Create a provider-neutral target for uploading one attachment object."""
        ...
