"""Tests for workspace/project navigation list contracts."""

from fastapi.routing import APIRoute
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.app import create_app
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization, Workspace
from taskmaster_backend.projects.models import Project
from taskmaster_backend.projects.routes import (
    list_workspace_projects_route,
    list_workspaces_route,
)
from taskmaster_backend.projects.schemas import (
    ProjectNavigationListResponse,
    WorkspaceNavigationListResponse,
)


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def _seed_navigation_records(session_factory: sessionmaker[Session]) -> tuple[str, str]:
    with session_factory() as session:
        organization = Organization(id="org-1", name="Acme")
        workspace_alpha = Workspace(
            id="workspace-1",
            organization_id="org-1",
            name="Alpha",
        )
        workspace_beta = Workspace(
            id="workspace-2",
            organization_id="org-1",
            name="Beta",
        )
        session.add_all(
            [
                organization,
                workspace_alpha,
                workspace_beta,
                Project(
                    id="project-2",
                    workspace_id="workspace-1",
                    key="OPS",
                    name="Operations",
                ),
                Project(
                    id="project-1",
                    workspace_id="workspace-1",
                    key="TM",
                    name="TaskMaster",
                ),
                Project(
                    id="project-3",
                    workspace_id="workspace-2",
                    key="WEB",
                    name="Website",
                ),
            ]
        )
        session.commit()
        return workspace_alpha.id, workspace_beta.id


def test_workspace_navigation_routes_are_registered() -> None:
    app = create_app()
    paths: dict[str, set[str]] = {}
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if route.path not in {
            "/api/v1/projects/workspaces",
            "/api/v1/projects/workspaces/{workspace_id}/projects",
        }:
            continue
        paths.setdefault(route.path, set()).update(route.methods)

    assert paths["/api/v1/projects/workspaces"] == {"GET"}
    assert paths["/api/v1/projects/workspaces/{workspace_id}/projects"] == {"GET", "POST"}


def test_workspace_navigation_openapi_contracts_are_exposed() -> None:
    app = create_app()
    openapi_schema = app.openapi()

    workspace_path = openapi_schema["paths"]["/api/v1/projects/workspaces"]["get"]
    project_path = openapi_schema["paths"][
        "/api/v1/projects/workspaces/{workspace_id}/projects"
    ]["get"]
    components = openapi_schema["components"]["schemas"]

    assert workspace_path["summary"] == "List workspaces for local navigation"
    assert project_path["summary"] == "List projects for a workspace for local navigation"
    assert "WorkspaceNavigationListResponse" in components
    assert "WorkspaceNavigationResponse" in components
    assert "ProjectNavigationListResponse" in components
    assert "ProjectNavigationResponse" in components


def test_list_workspaces_route_returns_sorted_navigation_records() -> None:
    session_factory = _create_test_session_factory()
    _seed_navigation_records(session_factory)

    with session_factory() as session:
        response = list_workspaces_route(session=session)

    assert isinstance(response, WorkspaceNavigationListResponse)
    assert [(item.id, item.name) for item in response.items] == [
        ("workspace-1", "Alpha"),
        ("workspace-2", "Beta"),
    ]


def test_list_workspace_projects_route_is_workspace_scoped() -> None:
    session_factory = _create_test_session_factory()
    workspace_alpha_id, _ = _seed_navigation_records(session_factory)

    with session_factory() as session:
        response = list_workspace_projects_route(
            workspace_alpha_id,
            session=session,
        )

    assert isinstance(response, ProjectNavigationListResponse)
    assert [(item.id, item.key) for item in response.items] == [
        ("project-2", "OPS"),
        ("project-1", "TM"),
    ]


def test_list_workspace_projects_route_returns_empty_list_for_workspace_without_projects() -> None:
    session_factory = _create_test_session_factory()
    _, workspace_beta_id = _seed_navigation_records(session_factory)

    with session_factory() as session:
        session.query(Project).filter(Project.workspace_id == workspace_beta_id).delete()
        session.commit()
        response = list_workspace_projects_route(
            workspace_beta_id,
            session=session,
        )

    assert isinstance(response, ProjectNavigationListResponse)
    assert response.items == []
