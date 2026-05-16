"""Tests for workflow transition validation."""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization, Workspace
from taskmaster_backend.projects.models import Project
from taskmaster_backend.work_items.models import WorkItem
from taskmaster_backend.workflows.models import (
    WorkflowAssignment,
    WorkflowDefinition,
    WorkflowState,
    WorkflowTransition,
    WorkflowTransitionRule,
)
from taskmaster_backend.workflows.validator import (
    MISSING_TRANSITION,
    MISSING_WORKFLOW_ASSIGNMENT,
    RULE_DENIED,
    SOURCE_STATE_MISMATCH,
    WORKFLOW_STATE_MISMATCH,
    WorkflowTransitionValidationRequest,
    validate_work_item_transition,
)


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def _seed_workflow(
    session_factory: sessionmaker[Session],
    *,
    with_assignment: bool = True,
    with_transition: bool = True,
    with_allowed_role_rule: bool = False,
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
            name="Operations",
        )
        workflow = WorkflowDefinition(
            id="workflow-1",
            project_id="project-1",
            name="Default",
            version=1,
        )
        other_workflow = WorkflowDefinition(
            id="workflow-2",
            project_id="project-2",
            name="Other",
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
        other_state = WorkflowState(
            id="state-other",
            workflow_definition_id="workflow-2",
            name="Other",
        )
        work_item = WorkItem(
            id="work-item-1",
            project_id="project-1",
            current_state_id="state-backlog",
            type="task",
            status="todo",
            title="Validate workflow",
            assignee_id="user-1",
            reporter_id="user-2",
            typed_metadata={"acceptance_criteria": "Defined"},
        )
        mismatched_work_item = WorkItem(
            id="work-item-mismatch",
            project_id="project-1",
            current_state_id="state-other",
            type="task",
            status="todo",
            title="Mismatched workflow state",
            typed_metadata={},
        )
        records: list[object] = [
            organization,
            workspace,
            primary_project,
            secondary_project,
            workflow,
            other_workflow,
            backlog,
            review,
            done,
            other_state,
            work_item,
            mismatched_work_item,
        ]

        if with_assignment:
            records.append(
                WorkflowAssignment(
                    id="assignment-1",
                    project_id="project-1",
                    workflow_definition_id="workflow-1",
                )
            )

        if with_transition:
            transition = WorkflowTransition(
                id="transition-1",
                workflow_definition_id="workflow-1",
                source_state_id="state-backlog",
                target_state_id="state-review",
            )
            records.append(transition)
            if with_allowed_role_rule:
                records.append(
                    WorkflowTransitionRule(
                        id="rule-1",
                        workflow_transition_id=transition.id,
                        rule_type="allowed_roles",
                        config={"roles": ["maintainer"]},
                    )
                )

        session.add_all(records)
        session.commit()

        return {
            "project_id": primary_project.id,
            "work_item_id": work_item.id,
            "mismatched_work_item_id": mismatched_work_item.id,
            "source_state_id": backlog.id,
            "target_state_id": review.id,
            "missing_target_state_id": done.id,
            "transition_id": "transition-1",
        }


def test_valid_transition_passes() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_workflow(session_factory)

    with session_factory() as session:
        result = validate_work_item_transition(
            session,
            WorkflowTransitionValidationRequest(
                project_id=ids["project_id"],
                work_item_id=ids["work_item_id"],
                source_state_id=ids["source_state_id"],
                target_state_id=ids["target_state_id"],
            ),
        )

    assert result.allowed is True
    assert result.error_code is None
    assert result.transition_id == ids["transition_id"]


def test_missing_workflow_assignment_fails_deterministically() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_workflow(session_factory, with_assignment=False)

    with session_factory() as session:
        result = validate_work_item_transition(
            session,
            WorkflowTransitionValidationRequest(
                project_id=ids["project_id"],
                work_item_id=ids["work_item_id"],
                target_state_id=ids["target_state_id"],
            ),
        )

    assert result.allowed is False
    assert result.error_code == MISSING_WORKFLOW_ASSIGNMENT


def test_missing_transition_fails_deterministically() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_workflow(session_factory, with_transition=False)

    with session_factory() as session:
        result = validate_work_item_transition(
            session,
            WorkflowTransitionValidationRequest(
                project_id=ids["project_id"],
                work_item_id=ids["work_item_id"],
                target_state_id=ids["target_state_id"],
            ),
        )

    assert result.allowed is False
    assert result.error_code == MISSING_TRANSITION


def test_missing_target_transition_fails_deterministically() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_workflow(session_factory)

    with session_factory() as session:
        result = validate_work_item_transition(
            session,
            WorkflowTransitionValidationRequest(
                project_id=ids["project_id"],
                work_item_id=ids["work_item_id"],
                target_state_id=ids["missing_target_state_id"],
            ),
        )

    assert result.allowed is False
    assert result.error_code == MISSING_TRANSITION


def test_source_state_mismatch_fails_deterministically() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_workflow(session_factory)

    with session_factory() as session:
        result = validate_work_item_transition(
            session,
            WorkflowTransitionValidationRequest(
                project_id=ids["project_id"],
                work_item_id=ids["work_item_id"],
                source_state_id="state-review",
                target_state_id=ids["target_state_id"],
            ),
        )

    assert result.allowed is False
    assert result.error_code == SOURCE_STATE_MISMATCH


def test_cross_project_workflow_mismatch_fails_deterministically() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_workflow(session_factory)

    with session_factory() as session:
        result = validate_work_item_transition(
            session,
            WorkflowTransitionValidationRequest(
                project_id=ids["project_id"],
                work_item_id=ids["mismatched_work_item_id"],
                target_state_id=ids["target_state_id"],
            ),
        )

    assert result.allowed is False
    assert result.error_code == WORKFLOW_STATE_MISMATCH


def test_rule_denied_transition_fails_deterministically() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_workflow(session_factory, with_allowed_role_rule=True)

    with session_factory() as session:
        result = validate_work_item_transition(
            session,
            WorkflowTransitionValidationRequest(
                project_id=ids["project_id"],
                work_item_id=ids["work_item_id"],
                target_state_id=ids["target_state_id"],
                actor_role_ids=frozenset({"viewer"}),
            ),
        )

    assert result.allowed is False
    assert result.error_code == RULE_DENIED
    assert result.transition_id == ids["transition_id"]
    assert result.rule_type == "allowed_roles"


def test_rule_allowed_transition_passes_when_actor_has_allowed_role() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_workflow(session_factory, with_allowed_role_rule=True)

    with session_factory() as session:
        result = validate_work_item_transition(
            session,
            WorkflowTransitionValidationRequest(
                project_id=ids["project_id"],
                work_item_id=ids["work_item_id"],
                target_state_id=ids["target_state_id"],
                actor_role_ids=frozenset({"maintainer"}),
            ),
        )

    assert result.allowed is True
    assert result.error_code is None
    assert result.transition_id == ids["transition_id"]


def test_transition_validation_does_not_mutate_work_item_state() -> None:
    session_factory = _create_test_session_factory()
    ids = _seed_workflow(session_factory)

    with session_factory() as session:
        result = validate_work_item_transition(
            session,
            WorkflowTransitionValidationRequest(
                project_id=ids["project_id"],
                work_item_id=ids["work_item_id"],
                target_state_id=ids["target_state_id"],
            ),
        )
        work_item = session.scalars(
            select(WorkItem).where(WorkItem.id == ids["work_item_id"])
        ).one()

    assert result.allowed is True
    assert work_item.current_state_id == ids["source_state_id"]
