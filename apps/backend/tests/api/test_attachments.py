"""Tests for attachment upload metadata endpoint behavior."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, cast

import pytest
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.app import create_app
from taskmaster_backend.attachments.routes import (
    create_attachment_upload,
    get_object_storage_adapter,
)
from taskmaster_backend.attachments.schemas import (
    AttachmentUploadCreateRequest,
    AttachmentUploadCreateResponse,
)
from taskmaster_backend.attachments.storage import (
    ObjectStorageUploadRequest,
    ObjectStorageUploadTarget,
)
from taskmaster_backend.collaboration.models import Attachment
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal
from taskmaster_backend.identity.models import Organization, User, Workspace
from taskmaster_backend.projects.models import Project
from taskmaster_backend.work_items.models import WorkItem


class RecordingStorageAdapter:
    def __init__(self) -> None:
        self.requests: list[ObjectStorageUploadRequest] = []
        self.error: Exception | None = None

    def create_upload_target(
        self,
        request: ObjectStorageUploadRequest,
    ) -> ObjectStorageUploadTarget:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return ObjectStorageUploadTarget(
            upload_url=f"https://storage.test/{request.storage_key}",
            storage_key=request.storage_key,
            expires_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            headers={"content-type": request.content_type},
        )


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def _seed_work_item(session_factory: sessionmaker[Session]) -> str:
    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        workspace = Workspace(id="workspace-1", organization_id="org-1", name="Platform")
        project = Project(id="project-1", workspace_id="workspace-1", key="TM", name="TaskMaster")
        user = User(
            id="user-123",
            email="user@example.com",
            password_hash="not-a-real-hash",
        )
        work_item = WorkItem(
            id="work-item-1",
            project_id="project-1",
            type="task",
            status="todo",
            title="Attachment target",
        )
        session.add_all([organization, workspace, project, user, work_item])
        session.commit()
        return work_item.id


def test_attachment_upload_route_is_registered_under_versioned_api() -> None:
    app = create_app()
    routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path == "/api/v1/projects/{project_id}/work-items/{work_item_id}/attachments"
    ]

    assert len(routes) == 1
    assert routes[0].methods == {"POST"}


def test_attachment_upload_persists_metadata_and_returns_upload_target() -> None:
    session_factory = _create_test_session_factory()
    work_item_id = _seed_work_item(session_factory)
    storage_adapter = RecordingStorageAdapter()
    request = AttachmentUploadCreateRequest(
        file_name="design.txt",
        content_type="text/plain",
        size_bytes=42,
    )

    with session_factory() as session:
        response = create_attachment_upload(
            "project-1",
            work_item_id,
            request,
            session,
            _principal(),
            storage_adapter,
        )

    assert isinstance(response, AttachmentUploadCreateResponse)
    assert response.attachment.work_item_id == work_item_id
    assert response.attachment.uploader_id == "user-123"
    assert response.attachment.file_name == "design.txt"
    assert response.attachment.content_type == "text/plain"
    assert response.attachment.size_bytes == 42
    assert response.upload.method == "PUT"
    assert response.upload.headers == {"content-type": "text/plain"}
    assert response.upload.upload_url.endswith(response.attachment.storage_key)
    assert storage_adapter.requests[0].storage_key == response.attachment.storage_key

    with session_factory() as session:
        attachment = session.scalars(select(Attachment)).one()
        assert attachment.id == response.attachment.id
        assert attachment.storage_key == response.attachment.storage_key


def test_attachment_upload_returns_not_found_for_unknown_work_item() -> None:
    session_factory = _create_test_session_factory()
    _seed_work_item(session_factory)
    request = AttachmentUploadCreateRequest(
        file_name="missing.txt",
        content_type="text/plain",
        size_bytes=1,
    )

    with session_factory() as session:
        response = create_attachment_upload(
            "project-1",
            "missing-work-item",
            request,
            session,
            _principal(),
            RecordingStorageAdapter(),
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert b"work_item_not_found" in response.body


def test_attachment_upload_validates_required_metadata() -> None:
    with pytest.raises(ValidationError):
        AttachmentUploadCreateRequest.model_validate(
            {"file_name": "", "content_type": "text/plain", "size_bytes": 1}
        )
    with pytest.raises(ValidationError):
        AttachmentUploadCreateRequest.model_validate(
            {"file_name": "design.txt", "content_type": "text/plain", "size_bytes": -1}
        )


def test_attachment_upload_rolls_back_when_storage_adapter_fails() -> None:
    session_factory = _create_test_session_factory()
    work_item_id = _seed_work_item(session_factory)
    storage_adapter = RecordingStorageAdapter()
    storage_adapter.error = RuntimeError("storage unavailable")
    request = AttachmentUploadCreateRequest(
        file_name="design.txt",
        content_type="text/plain",
        size_bytes=42,
    )

    with session_factory() as session:
        with pytest.raises(RuntimeError, match="storage unavailable"):
            create_attachment_upload(
                "project-1",
                work_item_id,
                request,
                session,
                _principal(),
                storage_adapter,
            )

    with session_factory() as session:
        assert session.scalars(select(Attachment)).all() == []


def test_default_storage_adapter_dependency_is_not_configured() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_object_storage_adapter()

    assert exc_info.value.status_code == 501
    detail = cast(dict[str, Any], exc_info.value.detail)
    assert detail["error_code"] == "object_storage_not_configured"


def test_attachment_upload_does_not_add_future_attachment_routes() -> None:
    app = create_app()
    attachment_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute) and "/attachments" in route.path
    ]

    assert len(attachment_routes) == 1
    assert attachment_routes[0].methods == {"POST"}


def _principal() -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        subject="user-123",
        issuer="test-issuer",
        audience="test-audience",
        expires_at=9_999_999_999,
    )
