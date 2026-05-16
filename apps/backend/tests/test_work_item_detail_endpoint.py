"""Tests for the WorkItem detail endpoint."""

from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.app import create_app
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization, Workspace
from taskmaster_backend.projects.models import Project
from taskmaster_backend.work_items.models import WorkItem
from taskmaster_backend.work_items.routes import get_project_work_item_detail
from taskmaster_backend.work_items.schemas import WorkItemResponse


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
            title="Primary work item",
            typed_metadata={"source": "seed"},
        )
        secondary_item = WorkItem(
            id="work-item-2",
            project_id="project-2",
            type="bug",
            status="open",
            title="Secondary work item",
            typed_metadata={},
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


def test_work_item_detail_route_is_registered_under_versioned_api() -> None:
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


def test_work_item_detail_route_openapi_contract_is_exposed() -> None:
    app = create_app()
    openapi_schema = app.openapi()
    path_item = openapi_schema["paths"]["/api/v1/projects/{project_id}/work-items/{work_item_id}"][
        "get"
    ]

    assert path_item["summary"] == "Get work item detail"
    assert "200" in path_item["responses"]
    assert "404" in path_item["responses"]

    components = openapi_schema["components"]["schemas"]
    assert "WorkItemResponse" in components
    assert "WorkItemApiErrorResponse" in components


def test_work_item_detail_returns_existing_project_scoped_work_item() -> None:
    session_factory = _create_test_session_factory()
    primary_project_id, _, primary_item_id, _ = _seed_projects_and_work_items(session_factory)

    with session_factory() as session:
        response = get_project_work_item_detail(primary_project_id, primary_item_id, session)

    assert isinstance(response, WorkItemResponse)
    assert response.id == primary_item_id
    assert response.project_id == primary_project_id
    assert response.type == "task"
    assert response.status == "todo"
    assert response.title == "Primary work item"
    assert response.typed_metadata == {"source": "seed"}


def test_work_item_detail_returns_not_found_for_missing_work_item() -> None:
    session_factory = _create_test_session_factory()
    primary_project_id, _, _, _ = _seed_projects_and_work_items(session_factory)

    with session_factory() as session:
        response = get_project_work_item_detail(primary_project_id, "missing-work-item", session)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert b"work_item_not_found" in response.body


def test_work_item_detail_does_not_return_item_from_another_project() -> None:
    session_factory = _create_test_session_factory()
    primary_project_id, _, _, secondary_item_id = _seed_projects_and_work_items(session_factory)

    with session_factory() as session:
        response = get_project_work_item_detail(primary_project_id, secondary_item_id, session)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert b"work_item_not_found" in response.body
