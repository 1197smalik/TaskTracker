"""Tests for the project workflow state catalog endpoint."""

from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.app import create_app
from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization, Workspace
from taskmaster_backend.projects.models import Project
from taskmaster_backend.projects.routes import list_project_workflow_states_route
from taskmaster_backend.projects.schemas import ProjectWorkflowStateCatalogResponse
from taskmaster_backend.workflows.models import (
    WorkflowAssignment,
    WorkflowDefinition,
    WorkflowState,
)


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def _seed_projects_and_workflows(
    session_factory: sessionmaker[Session],
) -> tuple[str, str, str]:
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
        unassigned_project = Project(
            id="project-3",
            workspace_id="workspace-1",
            key="NONE",
            name="Unassigned",
        )
        primary_workflow = WorkflowDefinition(
            id="workflow-1",
            project_id="project-1",
            name="Default",
            version=1,
        )
        secondary_workflow = WorkflowDefinition(
            id="workflow-2",
            project_id="project-2",
            name="Ops",
            version=1,
        )
        primary_states = [
            WorkflowState(
                id="state-review",
                workflow_definition_id="workflow-1",
                name="Review",
                position=20,
            ),
            WorkflowState(
                id="state-backlog",
                workflow_definition_id="workflow-1",
                name="Backlog",
                position=0,
            ),
            WorkflowState(
                id="state-beta",
                workflow_definition_id="workflow-1",
                name="Beta",
                position=10,
            ),
            WorkflowState(
                id="state-alpha",
                workflow_definition_id="workflow-1",
                name="Alpha",
                position=10,
            ),
            WorkflowState(
                id="state-done",
                workflow_definition_id="workflow-1",
                name="Done",
                position=30,
            ),
        ]
        secondary_state = WorkflowState(
            id="state-other",
            workflow_definition_id="workflow-2",
            name="Other",
            position=0,
        )
        session.add_all(
            [
                organization,
                workspace,
                primary_project,
                secondary_project,
                unassigned_project,
                primary_workflow,
                secondary_workflow,
                *primary_states,
                secondary_state,
                WorkflowAssignment(
                    project_id="project-1",
                    workflow_definition_id="workflow-1",
                ),
                WorkflowAssignment(
                    project_id="project-2",
                    workflow_definition_id="workflow-2",
                ),
            ]
        )
        session.commit()
        return primary_project.id, secondary_project.id, unassigned_project.id


def test_project_workflow_state_catalog_route_is_registered() -> None:
    app = create_app()
    routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path == "/api/v1/projects/{project_id}/workflow-states"
    ]

    assert len(routes) == 1
    assert routes[0].methods == {"GET"}


def test_project_workflow_state_catalog_openapi_contract_is_exposed() -> None:
    app = create_app()
    openapi_schema = app.openapi()
    path_item = openapi_schema["paths"][
        "/api/v1/projects/{project_id}/workflow-states"
    ]["get"]

    assert path_item["summary"] == "List project workflow states"
    assert "200" in path_item["responses"]
    assert "404" in path_item["responses"]

    components = openapi_schema["components"]["schemas"]
    assert "ProjectWorkflowStateCatalogResponse" in components
    assert "ProjectWorkflowStateResponse" in components
    assert "ProjectApiErrorResponse" in components


def test_project_workflow_state_catalog_returns_valid_project_mapping() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, _ = _seed_projects_and_workflows(session_factory)

    with session_factory() as session:
        response = list_project_workflow_states_route(project_id, session=session)

    assert isinstance(response, ProjectWorkflowStateCatalogResponse)
    assert response.workflow_definition_id == "workflow-1"
    assert [state.id for state in response.states] == [
        "state-backlog",
        "state-alpha",
        "state-beta",
        "state-review",
        "state-done",
    ]
    assert [state.position for state in response.states] == [0, 10, 10, 20, 30]


def test_project_workflow_state_catalog_returns_missing_assignment_error() -> None:
    session_factory = _create_test_session_factory()
    _, _, unassigned_project_id = _seed_projects_and_workflows(session_factory)

    with session_factory() as session:
        response = list_project_workflow_states_route(
            unassigned_project_id,
            session=session,
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert b"workflow_assignment_not_found" in response.body


def test_project_workflow_state_catalog_preserves_project_isolation() -> None:
    session_factory = _create_test_session_factory()
    primary_project_id, secondary_project_id, _ = _seed_projects_and_workflows(
        session_factory
    )

    with session_factory() as session:
        primary_response = list_project_workflow_states_route(
            primary_project_id,
            session=session,
        )
        secondary_response = list_project_workflow_states_route(
            secondary_project_id,
            session=session,
        )

    assert isinstance(primary_response, ProjectWorkflowStateCatalogResponse)
    assert isinstance(secondary_response, ProjectWorkflowStateCatalogResponse)
    assert {state.id for state in primary_response.states} == {
        "state-backlog",
        "state-alpha",
        "state-beta",
        "state-review",
        "state-done",
    }
    assert [state.id for state in secondary_response.states] == ["state-other"]
