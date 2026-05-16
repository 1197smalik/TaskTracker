"""Tests for the WorkItem transition endpoint."""

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
from taskmaster_backend.work_items.routes import transition_project_work_item_route
from taskmaster_backend.work_items.schemas import (
    WorkflowTransitionRequest,
    WorkflowTransitionResponse,
)
from taskmaster_backend.workflows.models import (
    WorkflowAssignment,
    WorkflowDefinition,
    WorkflowState,
    WorkflowTransition,
)


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def _seed_work_items_and_workflow(
    session_factory: sessionmaker[Session],
    *,
    with_assignment: bool = True,
) -> dict[str, str]:
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
        workflow = WorkflowDefinition(
            id="workflow-1",
            project_id="project-1",
            name="Default",
            version=1,
        )
        backlog = WorkflowState(
            id="state-backlog",
            workflow_definition_id="workflow-1",
            name="Backlog",
        )
        review = WorkflowState(
            id="state-review",
            workflow_definition_id="workflow-1",
            name="Review",
        )
        done = WorkflowState(
            id="state-done",
            workflow_definition_id="workflow-1",
            name="Done",
        )
        transition = WorkflowTransition(
            id="transition-1",
            workflow_definition_id="workflow-1",
            source_state_id="state-backlog",
            target_state_id="state-review",
        )
        primary_item = WorkItem(
            id="work-item-1",
            project_id="project-1",
            current_state_id="state-backlog",
            type="task",
            status="todo",
            title="Transition me",
            typed_metadata={},
            version=1,
        )
        secondary_item = WorkItem(
            id="work-item-2",
            project_id="project-2",
            current_state_id="state-backlog",
            type="task",
            status="todo",
            title="Cross project item",
            typed_metadata={},
            version=1,
        )
        records: list[object] = [
            organization,
            workspace,
            primary_project,
            secondary_project,
            workflow,
            backlog,
            review,
            done,
            transition,
            primary_item,
            secondary_item,
        ]
        if with_assignment:
            records.append(
                WorkflowAssignment(
                    id="assignment-1",
                    project_id="project-1",
                    workflow_definition_id="workflow-1",
                )
            )

        session.add_all(records)
        session.commit()

        return {
            "project_id": primary_project.id,
            "secondary_project_id": secondary_project.id,
            "work_item_id": primary_item.id,
            "secondary_work_item_id": secondary_item.id,
            "source_state_id": backlog.id,
            "target_state_id": review.id,
            "missing_transition_target_state_id": done.id,
            "transition_id": transition.id,
        }


def test_work_item_transition_route_is_registered_under_versioned_api() -> None:
    app = create_app()
    routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path
        == "/api/v1/projects/{project_id}/work-items/{work_item_id}/transition"
    ]

    assert len(routes) == 1
    assert routes[0].methods == {"POST"}


def test_work_item_transition_route_openapi_contract_is_exposed() -> None:
    app = create_app()
    openapi_schema = app.openapi()
    path_item = openapi_schema["paths"][
        "/api/v1/projects/{project_id}/work-items/{work_item_id}/transition"
    ]["post"]

    assert path_item["summary"] == "Transition work item"
    assert "requestBody" in path_item
    assert "200" in path_item["responses"]
    assert "400" in path_item["responses"]
    assert "404" in path_item["responses"]
    assert "409" in path_item["responses"]
    assert "422" in path_item["responses"]

    components = openapi_schema["components"]["schemas"]
    assert "WorkflowTransitionRequest" in components
    assert "WorkflowTransitionResponse" in components
    assert "WorkItemApiErrorResponse" in components
    assert set(components["WorkflowTransitionRequest"]["required"]) == {
        "expected_version",
        "target_state_id",
    }


def test_work_item_transition_updates_current_state_and_increments_version() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_work_items_and_workflow(session_factory)
    request = WorkflowTransitionRequest(
        expected_version=1,
        source_state_id=ids["source_state_id"],
        target_state_id=ids["target_state_id"],
    )

    with session_factory() as session:
        response = transition_project_work_item_route(
            ids["project_id"],
            ids["work_item_id"],
            request,
            session,
        )

    assert isinstance(response, WorkflowTransitionResponse)
    assert response.transition_id == ids["transition_id"]
    assert response.source_state_id == ids["source_state_id"]
    assert response.target_state_id == ids["target_state_id"]
    assert response.work_item.current_state_id == ids["target_state_id"]
    assert response.work_item.version == 2

    with session_factory() as session:
        work_item = session.scalars(
            select(WorkItem).where(WorkItem.id == ids["work_item_id"])
        ).one()
        assert work_item.current_state_id == ids["target_state_id"]
        assert work_item.version == 2


def test_work_item_transition_returns_not_found_for_missing_work_item() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_work_items_and_workflow(session_factory)
    request = WorkflowTransitionRequest(
        expected_version=1,
        target_state_id=ids["target_state_id"],
    )

    with session_factory() as session:
        response = transition_project_work_item_route(
            ids["project_id"],
            "missing-work-item",
            request,
            session,
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert b"work_item_not_found" in response.body


def test_work_item_transition_does_not_transition_item_from_another_project() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_work_items_and_workflow(session_factory)
    request = WorkflowTransitionRequest(
        expected_version=1,
        target_state_id=ids["target_state_id"],
    )

    with session_factory() as session:
        response = transition_project_work_item_route(
            ids["project_id"],
            ids["secondary_work_item_id"],
            request,
            session,
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert b"work_item_not_found" in response.body

    with session_factory() as session:
        work_item = session.scalars(
            select(WorkItem).where(WorkItem.id == ids["secondary_work_item_id"])
        ).one()
        assert work_item.current_state_id == ids["source_state_id"]
        assert work_item.version == 1


def test_work_item_transition_returns_conflict_for_stale_version() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_work_items_and_workflow(session_factory)
    request = WorkflowTransitionRequest(
        expected_version=2,
        target_state_id=ids["target_state_id"],
    )

    with session_factory() as session:
        response = transition_project_work_item_route(
            ids["project_id"],
            ids["work_item_id"],
            request,
            session,
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 409
    assert b"work_item_version_conflict" in response.body
    assert b"current_version" in response.body

    with session_factory() as session:
        work_item = session.scalars(
            select(WorkItem).where(WorkItem.id == ids["work_item_id"])
        ).one()
        assert work_item.current_state_id == ids["source_state_id"]
        assert work_item.version == 1


def test_work_item_transition_returns_bad_request_for_missing_workflow_assignment() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_work_items_and_workflow(session_factory, with_assignment=False)
    request = WorkflowTransitionRequest(
        expected_version=1,
        target_state_id=ids["target_state_id"],
    )

    with session_factory() as session:
        response = transition_project_work_item_route(
            ids["project_id"],
            ids["work_item_id"],
            request,
            session,
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert b"invalid_work_item_transition" in response.body
    assert b"missing_workflow_assignment" in response.body

    with session_factory() as session:
        work_item = session.scalars(
            select(WorkItem).where(WorkItem.id == ids["work_item_id"])
        ).one()
        assert work_item.current_state_id == ids["source_state_id"]
        assert work_item.version == 1


def test_work_item_transition_returns_bad_request_for_invalid_transition() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_work_items_and_workflow(session_factory)
    request = WorkflowTransitionRequest(
        expected_version=1,
        target_state_id=ids["missing_transition_target_state_id"],
    )

    with session_factory() as session:
        response = transition_project_work_item_route(
            ids["project_id"],
            ids["work_item_id"],
            request,
            session,
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert b"invalid_work_item_transition" in response.body
    assert b"missing_transition" in response.body

    with session_factory() as session:
        work_item = session.scalars(
            select(WorkItem).where(WorkItem.id == ids["work_item_id"])
        ).one()
        assert work_item.current_state_id == ids["source_state_id"]
        assert work_item.version == 1


def test_work_item_transition_returns_bad_request_for_source_state_mismatch() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_work_items_and_workflow(session_factory)
    request = WorkflowTransitionRequest(
        expected_version=1,
        source_state_id=ids["target_state_id"],
        target_state_id=ids["target_state_id"],
    )

    with session_factory() as session:
        response = transition_project_work_item_route(
            ids["project_id"],
            ids["work_item_id"],
            request,
            session,
        )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert b"invalid_work_item_transition" in response.body
    assert b"source_state_mismatch" in response.body

    with session_factory() as session:
        work_item = session.scalars(
            select(WorkItem).where(WorkItem.id == ids["work_item_id"])
        ).one()
        assert work_item.current_state_id == ids["source_state_id"]
        assert work_item.version == 1


def test_work_item_transition_validates_payload() -> None:
    with pytest.raises(ValidationError):
        WorkflowTransitionRequest.model_validate(
            {
                "target_state_id": "state-review",
            }
        )

    with pytest.raises(ValidationError):
        WorkflowTransitionRequest.model_validate(
            {
                "expected_version": 1,
                "target_state_id": "",
            }
        )
