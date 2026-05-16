"""Tests for workflow assignment to projects."""

from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    Index,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    select,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization, Workspace
from taskmaster_backend.projects.models import Project
from taskmaster_backend.workflows.models import WorkflowAssignment, WorkflowDefinition
from taskmaster_backend.workflows.repository import (
    PROJECT_NOT_FOUND,
    WORKFLOW_DEFINITION_NOT_FOUND,
    assign_project_workflow,
    get_project_workflow_assignment,
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
        primary_workflow = WorkflowDefinition(
            id="workflow-1",
            project_id="project-1",
            name="Default",
            version=1,
        )
        replacement_workflow = WorkflowDefinition(
            id="workflow-2",
            project_id="project-1",
            name="Updated",
            version=1,
        )
        secondary_workflow = WorkflowDefinition(
            id="workflow-3",
            project_id="project-2",
            name="Other",
            version=1,
        )
        session.add_all(
            [
                organization,
                workspace,
                primary_project,
                secondary_project,
                primary_workflow,
                replacement_workflow,
                secondary_workflow,
            ]
        )
        session.commit()
        return (
            primary_project.id,
            secondary_project.id,
            primary_workflow.id,
            replacement_workflow.id,
            secondary_workflow.id,
        )


def test_workflow_assignment_model_is_registered_with_base_metadata() -> None:
    assert WorkflowAssignment.__table__ is Base.metadata.tables["workflow_assignments"]


def test_workflow_assignment_model_has_expected_columns() -> None:
    columns = WorkflowAssignment.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "project_id",
        "workflow_definition_id",
        "created_at",
        "updated_at",
    }
    assert isinstance(columns["id"].type, String)
    assert isinstance(columns["project_id"].type, String)
    assert isinstance(columns["workflow_definition_id"].type, String)
    assert isinstance(columns["created_at"].type, DateTime)
    assert isinstance(columns["updated_at"].type, DateTime)


def test_workflow_assignment_model_has_project_scoped_constraints_and_indexes() -> None:
    table = WorkflowAssignment.__table__
    assert isinstance(table, Table)

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    ]
    foreign_key_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    index_columns: dict[str, tuple[str, ...]] = {
        str(index.name): tuple(column.name for column in index.columns)
        for index in table.indexes
        if isinstance(index, Index)
    }
    foreign_keys = {
        tuple(column.name for column in constraint.columns): tuple(
            element.target_fullname for element in constraint.elements
        )
        for constraint in foreign_key_constraints
    }

    assert any(
        constraint.name == "uq_workflow_assignments_project_id"
        and tuple(column.name for column in constraint.columns) == ("project_id",)
        for constraint in unique_constraints
    )
    assert foreign_keys[("project_id",)] == ("projects.id",)
    assert foreign_keys[("workflow_definition_id",)] == ("workflow_definitions.id",)
    assert index_columns["ix_workflow_assignments_project_id"] == ("project_id",)
    assert index_columns["ix_workflow_assignments_workflow_definition_id"] == (
        "workflow_definition_id",
    )
    assert index_columns[
        "ix_workflow_assignments_project_id_workflow_definition_id"
    ] == (
        "project_id",
        "workflow_definition_id",
    )


def test_assign_project_workflow_persists_valid_assignment() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, workflow_id, _, _ = _seed_projects_and_workflows(session_factory)

    with session_factory() as session:
        assignment, error = assign_project_workflow(session, project_id, workflow_id)

    assert error is None
    assert assignment is not None
    assert assignment.project_id == project_id
    assert assignment.workflow_definition_id == workflow_id

    with session_factory() as session:
        persisted = session.scalars(select(WorkflowAssignment)).one()
        assert persisted.project_id == project_id
        assert persisted.workflow_definition_id == workflow_id


def test_assign_project_workflow_replaces_existing_project_assignment() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, workflow_id, replacement_workflow_id, _ = _seed_projects_and_workflows(
        session_factory
    )

    with session_factory() as session:
        first_assignment, first_error = assign_project_workflow(
            session,
            project_id,
            workflow_id,
        )
        second_assignment, second_error = assign_project_workflow(
            session,
            project_id,
            replacement_workflow_id,
        )

    assert first_error is None
    assert second_error is None
    assert first_assignment is not None
    assert second_assignment is not None
    assert second_assignment.id == first_assignment.id
    assert second_assignment.workflow_definition_id == replacement_workflow_id

    with session_factory() as session:
        assignments = list(session.scalars(select(WorkflowAssignment)).all())
        assert len(assignments) == 1
        assert assignments[0].workflow_definition_id == replacement_workflow_id


def test_get_project_workflow_assignment_resolves_project_scoped_assignment() -> None:
    session_factory = _create_test_session_factory()
    project_id, secondary_project_id, workflow_id, _, _ = _seed_projects_and_workflows(
        session_factory
    )

    with session_factory() as session:
        assign_project_workflow(session, project_id, workflow_id)
        assignment = get_project_workflow_assignment(session, project_id)
        secondary_assignment = get_project_workflow_assignment(session, secondary_project_id)

    assert assignment is not None
    assert assignment.workflow_definition_id == workflow_id
    assert secondary_assignment is None


def test_assign_project_workflow_rejects_missing_project() -> None:
    session_factory = _create_test_session_factory()
    _, _, workflow_id, _, _ = _seed_projects_and_workflows(session_factory)

    with session_factory() as session:
        assignment, error = assign_project_workflow(
            session,
            "missing-project",
            workflow_id,
        )

    assert assignment is None
    assert error == PROJECT_NOT_FOUND


def test_assign_project_workflow_rejects_missing_workflow_definition() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, _, _, _ = _seed_projects_and_workflows(session_factory)

    with session_factory() as session:
        assignment, error = assign_project_workflow(
            session,
            project_id,
            "missing-workflow",
        )

    assert assignment is None
    assert error == WORKFLOW_DEFINITION_NOT_FOUND


def test_assign_project_workflow_rejects_cross_project_workflow_definition() -> None:
    session_factory = _create_test_session_factory()
    project_id, _, _, _, secondary_workflow_id = _seed_projects_and_workflows(
        session_factory
    )

    with session_factory() as session:
        assignment, error = assign_project_workflow(
            session,
            project_id,
            secondary_workflow_id,
        )

    assert assignment is None
    assert error == WORKFLOW_DEFINITION_NOT_FOUND

    with session_factory() as session:
        assignments = list(session.scalars(select(WorkflowAssignment)).all())
        assert assignments == []


def test_workflow_assignment_model_does_not_create_execution_fields() -> None:
    columns = WorkflowAssignment.__table__.columns

    assert "current_state_id" not in columns
    assert "transition_id" not in columns
    assert "rule_evaluator_id" not in columns
    assert "event_outbox_id" not in columns
    assert "automation_payload" not in columns
