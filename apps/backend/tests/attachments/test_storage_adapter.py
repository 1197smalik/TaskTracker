"""Tests for the object storage adapter contract."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from taskmaster_backend.attachments.storage import (
    ObjectStorageAdapter,
    ObjectStorageUploadRequest,
    ObjectStorageUploadTarget,
)


class RecordingStorageAdapter:
    """Concrete test double proving the protocol is implementable offline."""

    def __init__(self) -> None:
        self.requests: list[ObjectStorageUploadRequest] = []

    def create_upload_target(
        self,
        request: ObjectStorageUploadRequest,
    ) -> ObjectStorageUploadTarget:
        self.requests.append(request)
        return ObjectStorageUploadTarget(
            upload_url=f"https://storage.test/{request.storage_key}",
            storage_key=request.storage_key,
            expires_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            headers={"content-type": request.content_type},
        )


def test_upload_request_captures_required_storage_metadata() -> None:
    request = ObjectStorageUploadRequest(
        storage_key="attachments/work-item-1/file.txt",
        content_type="text/plain",
        size_bytes=42,
    )

    assert request.storage_key == "attachments/work-item-1/file.txt"
    assert request.content_type == "text/plain"
    assert request.size_bytes == 42
    assert request.expires_in_seconds == 900


@pytest.mark.parametrize(
    ("request_factory", "message"),
    [
        (
            lambda: ObjectStorageUploadRequest(
                storage_key="",
                content_type="text/plain",
                size_bytes=1,
            ),
            "storage_key",
        ),
        (
            lambda: ObjectStorageUploadRequest(
                storage_key="attachments/file.txt",
                content_type="",
                size_bytes=1,
            ),
            "content_type",
        ),
        (
            lambda: ObjectStorageUploadRequest(
                storage_key="attachments/file.txt",
                content_type="text/plain",
                size_bytes=-1,
            ),
            "size_bytes",
        ),
        (
            lambda: ObjectStorageUploadRequest(
                storage_key="attachments/file.txt",
                content_type="text/plain",
                size_bytes=1,
                expires_in_seconds=0,
            ),
            "expires_in_seconds",
        ),
    ],
)
def test_upload_request_rejects_invalid_values(
    request_factory: Callable[[], ObjectStorageUploadRequest],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        request_factory()


def test_upload_target_captures_provider_neutral_upload_fields() -> None:
    expires_at = datetime(2026, 1, 1, tzinfo=timezone.utc)

    target = ObjectStorageUploadTarget(
        upload_url="https://storage.test/upload",
        storage_key="attachments/work-item-1/file.txt",
        expires_at=expires_at,
        headers={"content-type": "text/plain"},
    )

    assert target.upload_url == "https://storage.test/upload"
    assert target.storage_key == "attachments/work-item-1/file.txt"
    assert target.expires_at == expires_at
    assert target.method == "PUT"
    assert target.headers == {"content-type": "text/plain"}


def test_storage_adapter_protocol_can_be_implemented_without_external_io() -> None:
    adapter: ObjectStorageAdapter = RecordingStorageAdapter()
    request = ObjectStorageUploadRequest(
        storage_key="attachments/work-item-1/file.txt",
        content_type="text/plain",
        size_bytes=42,
    )

    target = adapter.create_upload_target(request)

    assert target.storage_key == request.storage_key
    assert target.upload_url == "https://storage.test/attachments/work-item-1/file.txt"
    assert target.headers == {"content-type": "text/plain"}


def test_contract_objects_are_immutable() -> None:
    request = ObjectStorageUploadRequest(
        storage_key="attachments/work-item-1/file.txt",
        content_type="text/plain",
        size_bytes=42,
    )

    with pytest.raises(FrozenInstanceError):
        request.storage_key = "changed"  # type: ignore[misc]


def test_storage_contract_does_not_define_concrete_backend_behavior() -> None:
    adapter = RecordingStorageAdapter()

    assert not hasattr(adapter, "bucket_name")
    assert not hasattr(adapter, "s3_client")
    assert not hasattr(adapter, "upload_file")
    assert not hasattr(adapter, "download_file")
