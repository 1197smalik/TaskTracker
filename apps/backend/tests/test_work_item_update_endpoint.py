"""Tests for the WorkItem update endpoint."""

import pytest
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.app import create_app
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization, Workspace
from taskmaster_backend.projects.models import Project
from taskmaster_backend.work_items.models import WorkItem
from taskmaster_backend.work_items.routes import update_project_work_item_route
from taskmaster_backend.work_items.schemas import WorkItemResponse, WorkItemUpdateRequest


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def _seed_projects_and_work_items(
    session_factory: sessionmaker[Session],
) -> tuple[str, str, str, str]:
    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        workspace = Workspace(id="workspace-1", organization_id="org-1", name="Platform")
        primary_project = Project(
            id="project-1",
            workspace_id="workspace-1",
            key="TM",
            name="TaskMaster",
        )
        secondary_project = Project(
            id="project-2",
            workspace_id="workspace-1",
            key="OPS",
            name="Ops",
        )
        primary_item = WorkItem(
            id="work-item-1",
            project_id="project-1",
            type="task",
            status="todo",
            title="Original title",
            description="Original description",
            priority="medium",
            severity="low",
            estimate=2,
            typed_metadata={"source": "seed"},
            version=1,
        )
        secondary_item = WorkItem(
            id="work-item-2",
            project_id="project-2",
            type="bug",
            status="open",
            title="Secondary work item",
            typed_metadata={},
            version=1,
        )
        session.add_all(
            [
                organization,
                workspace,
                primary_project,
                secondary_project,
                primary_item,
                secondary_item,
            ]
        )
        session.commit()
        return (
            primary_project.id,
            secondary_project.id,
            primary_item.id,
            secondary_item.id,
        )


def test_work_item_update_route_is_registered_under_versioned_api() -> None:
    app = create_app()
    routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path == "/api/v1/projects/{project_id}/work-items/{work_item_id}"
    ]

    assert len(routes) == 2
    methods = {method for route in routes for method in route.methods}
    assert methods == {"GET", "PATCH"}


def test_work_item_update_route_openapi_contract_is_exposed() -> None:
    app = create_app()
    openapi_schema = app.openapi()
    path_item = openapi_schema["paths"]["/api/v1/projects/{project_id}/work-items/{work_item_id}"][
        "patch"
    ]

    assert path_item["summary"] == "Update work item"
    assert "requestBody" in path_item
    assert "200" in path_item["responses"]
    assert "404" in path_item["responses"]
    assert "409" in path_item["responses"]
    assert "422" in path_item["responses"]

    components = openapi_schema["components"]["schemas"]
    assert "WorkItemUpdateRequest" in components
    assert "WorkItemResponse" in components
    assert "WorkItemApiErrorResponse" in components
    assert set(components["WorkItemUpdateRequest"]["required"]) == {"expected_version"}


def test_work_item_update_modifies_allowed_fields_and_increments_version() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, work_item_id, _ = _seed_projects_and_work_items(session_factory)
    request = WorkItemUpdateRequest(
        expected_version=1,
        type="story",
        status="in_progress",
        title="Updated title",
        description="Updated description",
        priority="high",
        severity="medium",
        estimate=5,
        typed_metadata={"source": "updated"},
    )

    with session_factory() as session:
        response = update_project_work_item_route(project_id, work_item_id, request, session)

    assert isinstance(response, WorkItemResponse)
    assert response.id == work_item_id
    assert response.project_id == project_id
    assert response.type == "story"
    assert response.status == "in_progress"
    assert response.title == "Updated title"
    assert response.description == "Updated description"
    assert response.priority == "high"
    assert response.severity == "medium"
    assert response.estimate == 5
    assert response.typed_metadata == {"source": "updated"}
    assert response.version == 2

    with session_factory() as session:
        work_item = session.scalars(select(WorkItem).where(WorkItem.id == work_item_id)).one()
        assert work_item.title == "Updated title"
        assert work_item.version == 2


def test_work_item_update_returns_conflict_for_stale_version() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, work_item_id, _ = _seed_projects_and_work_items(session_factory)
    request = WorkItemUpdateRequest(expected_version=2, title="Stale update")

    with session_factory() as session:
        response = update_project_work_item_route(project_id, work_item_id, request, session)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 409
    assert b"work_item_version_conflict" in response.body
    assert b"current_version" in response.body

    with session_factory() as session:
        work_item = session.scalars(select(WorkItem).where(WorkItem.id == work_item_id)).one()
        assert work_item.title == "Original title"
        assert work_item.version == 1


def test_work_item_update_returns_not_found_for_missing_work_item() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, _, _ = _seed_projects_and_work_items(session_factory)
    request = WorkItemUpdateRequest(expected_version=1, title="Missing update")

    with session_factory() as session:
        response = update_project_work_item_route(project_id, "missing-work-item", request, session)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert b"work_item_not_found" in response.body


def test_work_item_update_does_not_update_item_from_another_project() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, _, secondary_item_id = _seed_projects_and_work_items(session_factory)
    request = WorkItemUpdateRequest(expected_version=1, title="Cross project update")

    with session_factory() as session:
        response = update_project_work_item_route(project_id, secondary_item_id, request, session)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert b"work_item_not_found" in response.body

    with session_factory() as session:
        work_item = session.scalars(select(WorkItem).where(WorkItem.id == secondary_item_id)).one()
        assert work_item.title == "Secondary work item"
        assert work_item.version == 1


def test_work_item_update_validates_payload() -> None:
    with pytest.raises(ValidationError):
        WorkItemUpdateRequest.model_validate({"title": "Missing expected version"})

    with pytest.raises(ValidationError):
        WorkItemUpdateRequest.model_validate({"expected_version": 1})

    with pytest.raises(ValidationError):
        WorkItemUpdateRequest.model_validate(
            {
                "expected_version": 1,
                "current_state_id": "workflow-state-1",
            }
        )

    with pytest.raises(ValidationError):
        WorkItemUpdateRequest.model_validate(
            {
                "expected_version": 1,
                "type": "feature",
            }
        )
