"""Tests for owner-based work item list visibility filtering."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import ANY

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.app import create_app
from taskmaster_backend.core import config as config_module
from taskmaster_backend.db.base import Base
from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.identity.models import Organization, User, Workspace
from taskmaster_backend.identity.passwords import hash_password
from taskmaster_backend.identity.tokens import create_access_token
from taskmaster_backend.projects.models import Project
from taskmaster_backend.work_items.models import WorkItem


@pytest.fixture()
def visibility_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    monkeypatch.setenv("TASKMASTER_JWT_SECRET", "test-secret-value-with-32-plus-bytes")
    monkeypatch.setenv("TASKMASTER_JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("TASKMASTER_JWT_ISSUER", "test-issuer")
    monkeypatch.setenv("TASKMASTER_JWT_AUDIENCE", "test-audience")
    monkeypatch.setenv("TASKMASTER_JWT_ACCESS_TOKEN_TTL_SECONDS", "900")
    config_module.reset_settings_cache()

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )

    app = create_app()

    def override_db_session() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_db_session

    with session_factory() as session:
        session.add_all(
            [
                User(
                    id="user-owner-1",
                    email="owner1@example.com",
                    password_hash=hash_password("secret"),
                ),
                User(
                    id="user-owner-2",
                    email="owner2@example.com",
                    password_hash=hash_password("secret"),
                ),
                Organization(
                    id="org-1",
                    name="Acme",
                    owner_user_id="user-owner-1",
                ),
                Organization(
                    id="org-2",
                    name="Globex",
                    owner_user_id="user-owner-2",
                ),
                Workspace(
                    id="workspace-1",
                    organization_id="org-1",
                    name="Alpha",
                ),
                Workspace(
                    id="workspace-2",
                    organization_id="org-2",
                    name="Beta",
                ),
                Project(
                    id="project-1",
                    workspace_id="workspace-1",
                    key="OPS",
                    name="Operations",
                ),
                Project(
                    id="project-2",
                    workspace_id="workspace-2",
                    key="WEB",
                    name="Website",
                ),
                WorkItem(
                    id="work-item-1",
                    project_id="project-1",
                    type="task",
                    status="todo",
                    title="Visible work item",
                    typed_metadata={},
                ),
                WorkItem(
                    id="work-item-2",
                    project_id="project-2",
                    type="bug",
                    status="todo",
                    title="Hidden work item",
                    typed_metadata={},
                ),
            ]
        )
        session.commit()

    with TestClient(app) as client:
        yield client


def test_work_item_list_requires_authenticated_principal(
    visibility_client: TestClient,
) -> None:
    response = visibility_client.get("/api/v1/projects/project-1/work-items")

    assert response.status_code == 401
    assert response.json()["detail"]["error_code"] == "missing_bearer_token"


def test_work_item_list_returns_items_for_owned_project(
    visibility_client: TestClient,
) -> None:
    response = visibility_client.get(
        "/api/v1/projects/project-1/work-items?limit=50&offset=0",
        headers={"Authorization": f"Bearer {create_access_token('user-owner-1')}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": "work-item-1",
                "project_id": "project-1",
                "parent_id": None,
                "sprint_id": None,
                "epic_id": None,
                "assignee_id": None,
                "reporter_id": None,
                "current_state_id": None,
                "type": "task",
                "status": "todo",
                "title": "Visible work item",
                "description": None,
                "priority": None,
                "severity": None,
                "estimate": None,
                "typed_metadata": {},
                "version": 1,
                "created_at": ANY,
                "updated_at": ANY,
            }
        ],
        "total": 1,
        "limit": 50,
        "offset": 0,
    }


def test_work_item_list_denies_inaccessible_project(
    visibility_client: TestClient,
) -> None:
    response = visibility_client.get(
        "/api/v1/projects/project-2/work-items",
        headers={"Authorization": f"Bearer {create_access_token('user-owner-1')}"},
    )

    assert response.status_code == 403
    body = response.json()
    assert body["error_code"] == "project_access_denied"
    assert body["message"] == "You are not authorized to access this project."


def test_work_item_list_returns_not_found_for_missing_project(
    visibility_client: TestClient,
) -> None:
    response = visibility_client.get(
        "/api/v1/projects/missing-project/work-items",
        headers={"Authorization": f"Bearer {create_access_token('user-owner-1')}"},
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "project_not_found"
