"""Tests for the WorkItem list endpoint."""

import pytest
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.app import create_app
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal
from taskmaster_backend.identity.models import Organization, Workspace
from taskmaster_backend.projects.models import Project
from taskmaster_backend.work_items.models import WorkItem
from taskmaster_backend.work_items.routes import list_project_work_items_route
from taskmaster_backend.work_items.schemas import WorkItemListParams, WorkItemListResponse


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def _principal(subject: str = "user-owner-1") -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        subject=subject,
        issuer="test-issuer",
        audience="test-audience",
        expires_at=4_102_444_800,
    )


def _seed_projects_and_work_items(
    session_factory: sessionmaker[Session],
) -> tuple[str, str, str]:
    with session_factory() as session:
        organization = Organization(
            id="org-1",
            name="Acme",
            owner_user_id="user-owner-1",
        )
        workspace = Workspace(id="workspace-1", organization_id="org-1", name="Platform")
        project_one = Project(
            id="project-1",
            workspace_id="workspace-1",
            key="TM",
            name="TaskMaster",
        )
        project_two = Project(
            id="project-2",
            workspace_id="workspace-1",
            key="OPS",
            name="Ops",
        )
        items = [
            WorkItem(
                id="work-item-1",
                project_id="project-1",
                type="task",
                status="todo",
                title="Alpha",
                typed_metadata={},
            ),
            WorkItem(
                id="work-item-2",
                project_id="project-1",
                type="bug",
                status="in_progress",
                title="Beta",
                typed_metadata={},
            ),
            WorkItem(
                id="work-item-3",
                project_id="project-1",
                type="story",
                status="done",
                title="Gamma",
                typed_metadata={},
            ),
            WorkItem(
                id="work-item-4",
                project_id="project-2",
                type="task",
                status="todo",
                title="Other",
                typed_metadata={},
            ),
        ]
        session.add_all([organization, workspace, project_one, project_two, *items])
        session.commit()
        return project_one.id, project_two.id, "empty-project"


def _seed_empty_project(session_factory: sessionmaker[Session], project_id: str) -> str:
    with session_factory() as session:
        project = Project(
            id=project_id,
            workspace_id="workspace-1",
            key="EMP",
            name="Empty",
        )
        session.add(project)
        session.commit()
        return project.id


def test_work_item_list_route_is_registered_under_versioned_api() -> None:
    app = create_app()
    routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path == "/api/v1/projects/{project_id}/work-items"
    ]

    assert len(routes) == 2
    methods = {method for route in routes for method in route.methods}
    assert methods == {"GET", "POST"}


def test_work_item_list_route_openapi_contract_is_exposed() -> None:
    app = create_app()
    openapi_schema = app.openapi()
    path_item = openapi_schema["paths"]["/api/v1/projects/{project_id}/work-items"]["get"]

    assert path_item["summary"] == "List work items"
    assert "200" in path_item["responses"]
    assert "401" in path_item["responses"]
    assert "403" in path_item["responses"]
    assert "404" in path_item["responses"]
    assert "422" in path_item["responses"]

    parameters = {parameter["name"]: parameter for parameter in path_item["parameters"]}
    assert parameters["limit"]["schema"]["default"] == 50
    assert parameters["limit"]["schema"]["minimum"] == 1
    assert parameters["limit"]["schema"]["maximum"] == 100
    assert parameters["offset"]["schema"]["default"] == 0
    assert parameters["offset"]["schema"]["minimum"] == 0

    components = openapi_schema["components"]["schemas"]
    assert "WorkItemListResponse" in components
    assert "WorkItemResponse" in components
    assert "WorkItemApiErrorResponse" in components


def test_work_item_list_returns_only_project_items() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, empty_project_id = _seed_projects_and_work_items(session_factory)
    _seed_empty_project(session_factory, empty_project_id)

    with session_factory() as session:
        response = list_project_work_items_route(
            project_id,
            limit=50,
            offset=0,
            session=session,
            principal=_principal(),
        )

    assert isinstance(response, WorkItemListResponse)
    assert response.total == 3
    assert response.limit == 50
    assert response.offset == 0
    assert [item.id for item in response.items] == [
        "work-item-1",
        "work-item-2",
        "work-item-3",
    ]


def test_work_item_list_returns_empty_list_for_project_with_no_items() -> None:
    session_factory = _create_test_session_factory()
    _, _, empty_project_id = _seed_projects_and_work_items(session_factory)
    _seed_empty_project(session_factory, empty_project_id)

    with session_factory() as session:
        response = list_project_work_items_route(
            empty_project_id,
            limit=50,
            offset=0,
            session=session,
            principal=_principal(),
        )

    assert isinstance(response, WorkItemListResponse)
    assert response.items == []
    assert response.total == 0
    assert response.limit == 50
    assert response.offset == 0


def test_work_item_list_applies_limit_and_offset_pagination() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, _ = _seed_projects_and_work_items(session_factory)

    with session_factory() as session:
        response = list_project_work_items_route(
            project_id,
            limit=2,
            offset=1,
            session=session,
            principal=_principal(),
        )

    assert isinstance(response, WorkItemListResponse)
    assert response.total == 3
    assert response.limit == 2
    assert response.offset == 1
    assert [item.id for item in response.items] == ["work-item-2", "work-item-3"]


def test_work_item_list_maintains_cross_project_isolation() -> None:
    session_factory = _create_test_session_factory()
    _, project_two_id, _ = _seed_projects_and_work_items(session_factory)

    with session_factory() as session:
        response = list_project_work_items_route(
            project_two_id,
            limit=50,
            offset=0,
            session=session,
            principal=_principal(),
        )

    assert isinstance(response, WorkItemListResponse)
    assert response.total == 1
    assert [item.id for item in response.items] == ["work-item-4"]


def test_work_item_list_validates_pagination_inputs() -> None:
    with pytest.raises(ValidationError):
        WorkItemListParams(limit=0, offset=0)

    with pytest.raises(ValidationError):
        WorkItemListParams(limit=101, offset=0)

    with pytest.raises(ValidationError):
        WorkItemListParams(limit=10, offset=-1)


def test_work_item_list_returns_not_found_for_missing_project() -> None:
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        response = list_project_work_items_route(
            "missing-project",
            limit=50,
            offset=0,
            session=session,
            principal=_principal(),
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert b"project_not_found" in response.body
