"""Tests for the WorkItem create endpoint."""

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
from taskmaster_backend.work_items.routes import create_project_work_item
from taskmaster_backend.work_items.schemas import WorkItemCreateRequest, WorkItemResponse


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def _seed_project(session_factory: sessionmaker[Session]) -> str:
    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        workspace = Workspace(id="workspace-1", organization_id="org-1", name="Platform")
        project = Project(id="project-1", workspace_id="workspace-1", key="TM", name="TaskMaster")
        session.add_all([organization, workspace, project])
        session.commit()
        return project.id


def test_work_item_create_route_is_registered_under_versioned_api() -> None:
    app = create_app()
    routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path == "/api/v1/projects/{project_id}/work-items"
    ]

    assert len(routes) == 1
    assert routes[0].methods == {"POST"}


def test_work_item_create_route_openapi_contract_is_exposed() -> None:
    app = create_app()
    openapi_schema = app.openapi()
    path_item = openapi_schema["paths"]["/api/v1/projects/{project_id}/work-items"]["post"]

    assert path_item["summary"] == "Create work item"
    assert "requestBody" in path_item
    assert "201" in path_item["responses"]
    assert "404" in path_item["responses"]
    assert "422" in path_item["responses"]

    components = openapi_schema["components"]["schemas"]
    assert "WorkItemCreateRequest" in components
    assert "WorkItemResponse" in components
    assert "WorkItemApiErrorResponse" in components
    assert set(components["WorkItemCreateRequest"]["required"]) == {
        "type",
        "status",
        "title",
    }


def test_work_item_create_persists_row_and_returns_created_response() -> None:
    session_factory = _create_test_session_factory()
    project_id = _seed_project(session_factory)
    request = WorkItemCreateRequest(
        type="task",
        status="todo",
        title="Write create endpoint",
        description="Persist the generic work item.",
        priority="high",
        severity="medium",
        estimate=3,
        typed_metadata={"source": "test"},
    )

    with session_factory() as session:
        response = create_project_work_item(project_id, request, session)

    assert isinstance(response, WorkItemResponse)
    assert response.project_id == project_id
    assert response.type == "task"
    assert response.status == "todo"
    assert response.title == "Write create endpoint"
    assert response.description == "Persist the generic work item."
    assert response.priority == "high"
    assert response.severity == "medium"
    assert response.estimate == 3
    assert response.typed_metadata == {"source": "test"}
    assert response.version == 1
    assert response.id
    assert response.created_at
    assert response.updated_at

    with session_factory() as session:
        work_item = session.scalars(select(WorkItem)).one()
        assert work_item.id == response.id
        assert work_item.project_id == project_id
        assert work_item.title == "Write create endpoint"


def test_work_item_create_validates_required_fields() -> None:
    with pytest.raises(ValidationError):
        WorkItemCreateRequest.model_validate({"type": "task", "status": "todo"})


def test_work_item_create_rejects_unsupported_type() -> None:
    with pytest.raises(ValidationError):
        WorkItemCreateRequest.model_validate(
            {"type": "feature", "status": "todo", "title": "Invalid type"}
        )


def test_work_item_create_returns_not_found_for_unknown_project() -> None:
    session_factory = _create_test_session_factory()
    request = WorkItemCreateRequest(
        type="task",
        status="todo",
        title="Unknown project",
    )

    with session_factory() as session:
        response = create_project_work_item("missing-project", request, session)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert b"project_not_found" in response.body


def test_work_item_routes_do_not_add_detail_list_or_update_endpoints() -> None:
    app = create_app()
    work_item_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute) and "/work-items" in route.path
    ]

    route_map = {route.path: route.methods for route in work_item_routes}

    assert route_map["/api/v1/projects/{project_id}/work-items"] == {"POST"}
    assert route_map["/api/v1/projects/{project_id}/work-items/{work_item_id}"] == {"GET"}
    assert len(work_item_routes) == 2
