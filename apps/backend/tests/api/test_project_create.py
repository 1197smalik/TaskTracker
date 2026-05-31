"""Tests for project creation endpoint behavior."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
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


@pytest.fixture()
def project_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
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
                    id="user-owner",
                    email="owner@example.com",
                    password_hash=hash_password("secret"),
                ),
                User(
                    id="user-other",
                    email="other@example.com",
                    password_hash=hash_password("secret"),
                ),
                Organization(
                    id="org-1",
                    name="Acme",
                    owner_user_id="user-owner",
                ),
                Workspace(
                    id="workspace-1",
                    organization_id="org-1",
                    name="Platform",
                ),
            ]
        )
        session.commit()

    with TestClient(app) as client:
        yield client, session_factory


def test_project_create_route_is_registered() -> None:
    app = create_app()
    matching_routes = [
        route.methods
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path == "/api/v1/projects/workspaces/{workspace_id}/projects"
    ]

    assert {"POST"} in matching_routes


def test_create_project_requires_authenticated_principal(
    project_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = project_client

    response = client.post(
        "/api/v1/projects/workspaces/workspace-1/projects",
        json={"key": "TM", "name": "TaskMaster"},
    )

    assert response.status_code == 401
    assert response.json()["detail"]["error_code"] == "missing_bearer_token"


def test_create_project_persists_project_for_workspace_owner(
    project_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = project_client

    response = client.post(
        "/api/v1/projects/workspaces/workspace-1/projects",
        headers={"Authorization": f"Bearer {create_access_token('user-owner')}"},
        json={"key": " tm ", "name": "  TaskMaster  "},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["project"]["id"] != ""
    assert body["project"]["workspace_id"] == "workspace-1"
    assert body["project"]["key"] == "TM"
    assert body["project"]["name"] == "TaskMaster"
    assert body["project"]["created_at"] != ""
    assert body["project"]["updated_at"] != ""

    with session_factory() as session:
        projects = session.scalars(select(Project)).all()

    assert len(projects) == 1
    assert projects[0].workspace_id == "workspace-1"
    assert projects[0].key == "TM"
    assert projects[0].name == "TaskMaster"


def test_create_project_rejects_invalid_workspace(
    project_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = project_client

    response = client.post(
        "/api/v1/projects/workspaces/workspace-missing/projects",
        headers={"Authorization": f"Bearer {create_access_token('user-owner')}"},
        json={"key": "TM", "name": "TaskMaster"},
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "workspace_not_found"


def test_create_project_rejects_unauthorized_workspace_access(
    project_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = project_client

    response = client.post(
        "/api/v1/projects/workspaces/workspace-1/projects",
        headers={"Authorization": f"Bearer {create_access_token('user-other')}"},
        json={"key": "TM", "name": "TaskMaster"},
    )

    assert response.status_code == 403
    body = response.json()
    assert body["error_code"] == "workspace_access_denied"
    assert body["message"] == "You are not authorized to access this workspace."


def test_create_project_rejects_invalid_project_data(
    project_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = project_client

    response = client.post(
        "/api/v1/projects/workspaces/workspace-1/projects",
        headers={"Authorization": f"Bearer {create_access_token('user-owner')}"},
        json={"key": "A!", "name": " "},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error_code"] == "invalid_project_key"
    assert body["field_errors"] == {"key": ["Use letters, numbers, or hyphens only."]}


def test_create_project_rejects_duplicate_project_name(
    project_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = project_client

    with session_factory() as session:
        session.add(
            Project(
                id="project-1",
                workspace_id="workspace-1",
                key="OPS",
                name="Operations",
            )
        )
        session.commit()

    response = client.post(
        "/api/v1/projects/workspaces/workspace-1/projects",
        headers={"Authorization": f"Bearer {create_access_token('user-owner')}"},
        json={"key": "TM", "name": " operations "},
    )

    assert response.status_code == 409
    body = response.json()
    assert body["error_code"] == "duplicate_project_name"
    assert body["field_errors"] == {"name": ["Use a unique project name."]}
