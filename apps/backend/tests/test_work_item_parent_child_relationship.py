"""Tests for WorkItem parent-child relationships."""

from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization, Workspace
from taskmaster_backend.projects.models import Project
from taskmaster_backend.work_items.models import WorkItem
from taskmaster_backend.work_items.routes import (
    create_project_work_item,
    update_project_work_item_route,
)
from taskmaster_backend.work_items.schemas import (
    WorkItemCreateRequest,
    WorkItemResponse,
    WorkItemUpdateRequest,
)


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
) -> tuple[str, str, str, str, str]:
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
        parent = WorkItem(
            id="parent-item",
            project_id="project-1",
            type="story",
            status="todo",
            title="Parent",
            typed_metadata={},
        )
        child = WorkItem(
            id="child-item",
            project_id="project-1",
            parent_id="parent-item",
            type="task",
            status="todo",
            title="Child",
            typed_metadata={},
        )
        cross_project_parent = WorkItem(
            id="other-parent",
            project_id="project-2",
            type="story",
            status="todo",
            title="Other parent",
            typed_metadata={},
        )
        session.add_all(
            [
                organization,
                workspace,
                primary_project,
                secondary_project,
                parent,
                child,
                cross_project_parent,
            ]
        )
        session.commit()
        return (
            primary_project.id,
            secondary_project.id,
            parent.id,
            child.id,
            cross_project_parent.id,
        )


def test_work_item_create_accepts_same_project_parent() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, parent_id, _, _ = _seed_projects_and_work_items(session_factory)
    request = WorkItemCreateRequest(
        type="task",
        status="todo",
        title="New child",
        parent_id=parent_id,
    )

    with session_factory() as session:
        response = create_project_work_item(project_id, request, session)

    assert isinstance(response, WorkItemResponse)
    assert response.parent_id == parent_id

    with session_factory() as session:
        work_item = session.scalars(
            select(WorkItem).where(WorkItem.id == response.id)
        ).one()
        assert work_item.parent_id == parent_id


def test_work_item_create_rejects_cross_project_parent() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, _, _, cross_project_parent_id = _seed_projects_and_work_items(session_factory)
    request = WorkItemCreateRequest(
        type="task",
        status="todo",
        title="Invalid child",
        parent_id=cross_project_parent_id,
    )

    with session_factory() as session:
        response = create_project_work_item(project_id, request, session)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert b"invalid_work_item_parent" in response.body
    assert b"parent_not_found" in response.body


def test_work_item_update_accepts_same_project_parent() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, parent_id, child_id, _ = _seed_projects_and_work_items(session_factory)
    request = WorkItemUpdateRequest(expected_version=1, parent_id=None)

    with session_factory() as session:
        cleared_response = update_project_work_item_route(project_id, child_id, request, session)

    assert isinstance(cleared_response, WorkItemResponse)
    assert cleared_response.parent_id is None
    assert cleared_response.version == 2

    with session_factory() as session:
        response = update_project_work_item_route(
            project_id,
            child_id,
            WorkItemUpdateRequest(expected_version=2, parent_id=parent_id),
            session,
        )

    assert isinstance(response, WorkItemResponse)
    assert response.parent_id == parent_id
    assert response.version == 3


def test_work_item_update_rejects_self_parent() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, parent_id, _, _ = _seed_projects_and_work_items(session_factory)
    request = WorkItemUpdateRequest(expected_version=1, parent_id=parent_id)

    with session_factory() as session:
        response = update_project_work_item_route(project_id, parent_id, request, session)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert b"invalid_work_item_parent" in response.body
    assert b"self_parent" in response.body


def test_work_item_update_rejects_cross_project_parent() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, _, child_id, cross_project_parent_id = _seed_projects_and_work_items(
        session_factory
    )
    request = WorkItemUpdateRequest(expected_version=1, parent_id=cross_project_parent_id)

    with session_factory() as session:
        response = update_project_work_item_route(project_id, child_id, request, session)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert b"invalid_work_item_parent" in response.body
    assert b"parent_not_found" in response.body


def test_work_item_update_rejects_obvious_cycle() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, parent_id, child_id, _ = _seed_projects_and_work_items(session_factory)
    request = WorkItemUpdateRequest(expected_version=1, parent_id=child_id)

    with session_factory() as session:
        response = update_project_work_item_route(project_id, parent_id, request, session)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert b"invalid_work_item_parent" in response.body
    assert b"cycle" in response.body


def test_work_item_response_includes_parent_metadata() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, parent_id, child_id, _ = _seed_projects_and_work_items(session_factory)

    with session_factory() as session:
        response = update_project_work_item_route(
            project_id,
            child_id,
            WorkItemUpdateRequest(expected_version=1, title="Child renamed"),
            session,
        )

    assert isinstance(response, WorkItemResponse)
    assert response.parent_id == parent_id
