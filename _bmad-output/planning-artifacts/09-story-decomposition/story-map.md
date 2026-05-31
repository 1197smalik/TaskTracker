# Story Map
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Story Decomposition Standard
Each story is intentionally small enough for autonomous execution, review, and rollback. Stories should take roughly 30–90 minutes each. No story should hide an entire subsystem behind a vague title.

## Epics
1. Platform Foundation
2. Identity and RBAC
3. Project Planning
4. Work Items
5. Workflow Engine
6. Audit and Events
7. Collaboration and Notifications
8. Integrations
9. Realtime
10. Frontend Experience
11. Observability and Production Readiness

## Stories
### TM-001: Create repository planning-to-implementation boundary checklist
**Estimate:** 30–90 minutes  
**Dependencies:** None  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `make validate-docs`
### TM-002: Create backend project skeleton with FastAPI health boundary defined
**Estimate:** 30–90 minutes  
**Dependencies:** TM-001  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `ruff check . && mypy . && pytest`
### TM-003: Create frontend Vite TypeScript skeleton with routing shell defined
**Estimate:** 30–90 minutes  
**Dependencies:** TM-001  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `npm run lint && npm run typecheck && npm run build`
### TM-004: Create Docker Compose baseline for app, db, redis, nginx
**Estimate:** 30–90 minutes  
**Dependencies:** TM-001  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `docker compose config && docker compose build`
### TM-005: Create SQLAlchemy base metadata and database session lifecycle
**Estimate:** 30–90 minutes  
**Dependencies:** TM-002  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/database`
### TM-006: Create Alembic migration baseline
**Estimate:** 30–90 minutes  
**Dependencies:** TM-005  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `alembic upgrade head && alembic downgrade -1`
### TM-007: Create User SQLAlchemy model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-005  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/identity`
### TM-008: Add Alembic migration for users table
**Estimate:** 30–90 minutes  
**Dependencies:** TM-007  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `alembic upgrade head`
### TM-009: Create Organization SQLAlchemy model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-007  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/identity`
### TM-010: Add Alembic migration for organizations table
**Estimate:** 30–90 minutes  
**Dependencies:** TM-009  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `alembic upgrade head`
### TM-011: Create Workspace SQLAlchemy model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-009  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/identity`
### TM-012: Add Alembic migration for workspaces table
**Estimate:** 30–90 minutes  
**Dependencies:** TM-011  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `alembic upgrade head`
### TM-013: Create Membership SQLAlchemy model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-011  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/identity`
### TM-014: Add Alembic migration for memberships table
**Estimate:** 30–90 minutes  
**Dependencies:** TM-013  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `alembic upgrade head`
### TM-015: Create Role and Permission SQLAlchemy models
**Estimate:** 30–90 minutes  
**Dependencies:** TM-013  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/rbac`
### TM-016: Add Alembic migration for roles and permissions
**Estimate:** 30–90 minutes  
**Dependencies:** TM-015  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `alembic upgrade head`
### TM-017: Create password hashing utility
**Estimate:** 30–90 minutes  
**Dependencies:** TM-007  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/security/test_passwords.py`
### TM-018: Create JWT access token utility
**Estimate:** 30–90 minutes  
**Dependencies:** TM-017  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/security/test_jwt.py`
### TM-019: Create refresh token persistence model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-018  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/security/test_refresh_tokens.py`
### TM-020: Implement login endpoint contract
**Estimate:** 30–90 minutes  
**Dependencies:** TM-018, TM-019  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/api/test_auth_login.py`
### TM-021: Implement refresh token endpoint contract
**Estimate:** 30–90 minutes  
**Dependencies:** TM-019  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/api/test_auth_refresh.py`
### TM-022: Implement logout/revocation endpoint contract
**Estimate:** 30–90 minutes  
**Dependencies:** TM-019  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/api/test_auth_logout.py`
### TM-023: Create RBAC permission evaluator service
**Estimate:** 30–90 minutes  
**Dependencies:** TM-015  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/rbac/test_evaluator.py`
### TM-024: Add FastAPI auth dependency
**Estimate:** 30–90 minutes  
**Dependencies:** TM-018, TM-023  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/api/test_auth_dependency.py`
### TM-025: Add RBAC middleware/dependency for scoped endpoints
**Estimate:** 30–90 minutes  
**Dependencies:** TM-023, TM-024  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/api/test_rbac_dependency.py`
### TM-026: Create Project SQLAlchemy model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-011  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/project`
### TM-027: Add Alembic migration for projects table
**Estimate:** 30–90 minutes  
**Dependencies:** TM-026  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `alembic upgrade head`
### TM-028: Create Board SQLAlchemy model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-026  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/project/test_boards.py`
### TM-029: Add Alembic migration for boards table
**Estimate:** 30–90 minutes  
**Dependencies:** TM-028  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `alembic upgrade head`
### TM-030: Create Sprint SQLAlchemy model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-026  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/project/test_sprints.py`
### TM-031: Create Epic SQLAlchemy model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-026  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/project/test_epics.py`
### TM-032: Create Label model and project label endpoints
**Estimate:** 30–90 minutes  
**Dependencies:** TM-026  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/project/test_labels.py`
### TM-033: Create Component model and project component endpoints
**Estimate:** 30–90 minutes  
**Dependencies:** TM-026  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/project/test_components.py`
### TM-034: Create Version model and project version endpoints
**Estimate:** 30–90 minutes  
**Dependencies:** TM-026  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/project/test_versions.py`
### TM-035: Create generic WorkItem SQLAlchemy model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-026  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/work_items/test_model.py`
### TM-036: Add Alembic migration for work_items table
**Estimate:** 30–90 minutes  
**Dependencies:** TM-035  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `alembic upgrade head`
### TM-037: Create WorkItem create endpoint
**Estimate:** 30–90 minutes  
**Dependencies:** TM-035, TM-025  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/api/test_work_item_create.py`
### TM-038: Create WorkItem detail endpoint
**Estimate:** 30–90 minutes  
**Dependencies:** TM-037  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/api/test_work_item_detail.py`
### TM-039: Create WorkItem list endpoint with project-scoped pagination
**Estimate:** 30–90 minutes  
**Dependencies:** TM-037  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/api/test_work_item_list.py`
### TM-040: Create WorkItem update endpoint with optimistic version check
**Estimate:** 30–90 minutes  
**Dependencies:** TM-037  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/api/test_work_item_update.py`
### TM-041: Create work item parent-child relationship support
**Estimate:** 30–90 minutes  
**Dependencies:** TM-035  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/work_items/test_hierarchy.py`
### TM-042: Create WorkflowDefinition model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-026  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/workflow/test_definition.py`
### TM-043: Create WorkflowState model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-042  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/workflow/test_states.py`
### TM-044: Create WorkflowTransition model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-043  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/workflow/test_transitions.py`
### TM-045: Create workflow transition rule model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-044  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/workflow/test_rules.py`
### TM-046: Add Alembic migrations for workflow tables
**Estimate:** 30–90 minutes  
**Dependencies:** TM-042, TM-043, TM-044, TM-045  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `alembic upgrade head`
### TM-047: Create workflow assignment to project
**Estimate:** 30–90 minutes  
**Dependencies:** TM-042, TM-026  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/workflow/test_assignment.py`
### TM-048: Create workflow transition validator service
**Estimate:** 30–90 minutes  
**Dependencies:** TM-044, TM-045, TM-023  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/workflow/test_validator.py`
### TM-049: Create work item transition endpoint
**Estimate:** 30–90 minutes  
**Dependencies:** TM-048, TM-037  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/api/test_work_item_transition.py`
### TM-050: Create audit log SQLAlchemy model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-009  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/audit/test_model.py`
### TM-051: Add Alembic migration for audit_logs table
**Estimate:** 30–90 minutes  
**Dependencies:** TM-050  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `alembic upgrade head`
### TM-052: Create audit writer service
**Estimate:** 30–90 minutes  
**Dependencies:** TM-050  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/audit/test_writer.py`
### TM-053: Add audit logging to work item creation
**Estimate:** 30–90 minutes  
**Dependencies:** TM-052, TM-037  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/audit/test_work_item_audit.py`
### TM-054: Add audit logging to workflow transition
**Estimate:** 30–90 minutes  
**Dependencies:** TM-052, TM-049  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/audit/test_transition_audit.py`
### TM-055: Create entity versioning model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-050  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/audit/test_entity_versions.py`
### TM-056: Create event outbox model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-050  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/events/test_outbox_model.py`
### TM-057: Add outbox event creation service
**Estimate:** 30–90 minutes  
**Dependencies:** TM-056  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/events/test_outbox_service.py`
### TM-058: Emit work_item.created event
**Estimate:** 30–90 minutes  
**Dependencies:** TM-057, TM-037  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/events/test_work_item_created.py`
### TM-059: Emit work_item.transitioned event
**Estimate:** 30–90 minutes  
**Dependencies:** TM-057, TM-049  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/events/test_work_item_transitioned.py`
### TM-060: Create background worker bootstrap
**Estimate:** 30–90 minutes  
**Dependencies:** TM-004, TM-056  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/workers`
### TM-061: Create outbox dispatcher worker
**Estimate:** 30–90 minutes  
**Dependencies:** TM-060, TM-057  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/events/test_dispatcher.py`
### TM-062: Create Comment SQLAlchemy model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-035  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/collaboration/test_comments.py`
### TM-063: Create comment create endpoint
**Estimate:** 30–90 minutes  
**Dependencies:** TM-062, TM-025  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/api/test_comments.py`
### TM-064: Create mention extraction service
**Estimate:** 30–90 minutes  
**Dependencies:** TM-063  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/collaboration/test_mentions.py`
### TM-065: Create Notification SQLAlchemy model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-064  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/notifications/test_model.py`
### TM-066: Create notification creation worker
**Estimate:** 30–90 minutes  
**Dependencies:** TM-065, TM-061  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/notifications/test_worker.py`
### TM-067: Create notification list/read endpoints
**Estimate:** 30–90 minutes  
**Dependencies:** TM-065  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/api/test_notifications.py`
### TM-068: Create attachment metadata model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-035  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/attachments/test_model.py`
### TM-069: Create object storage adapter contract
**Estimate:** 30–90 minutes  
**Dependencies:** TM-068  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/attachments/test_storage_adapter.py`
### TM-070: Create attachment upload metadata endpoint
**Estimate:** 30–90 minutes  
**Dependencies:** TM-068, TM-069  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/api/test_attachments.py`
### TM-071: Create activity event model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-035  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/activity/test_model.py`
### TM-072: Create activity writer service
**Estimate:** 30–90 minutes  
**Dependencies:** TM-071  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/activity/test_writer.py`
### TM-073: Add activity events for comments and transitions
**Estimate:** 30–90 minutes  
**Dependencies:** TM-072, TM-063, TM-049  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/activity`
### TM-074: Create API token model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-015  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/integrations/test_api_tokens.py`
### TM-075: Create API token generation and hashing utility
**Estimate:** 30–90 minutes  
**Dependencies:** TM-074  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/security/test_api_token_hashing.py`
### TM-076: Create API token management endpoints
**Estimate:** 30–90 minutes  
**Dependencies:** TM-074, TM-075  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/api/test_api_tokens.py`
### TM-077: Create WebhookEndpoint model
**Estimate:** 30–90 minutes  
**Dependencies:** TM-056  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/webhooks/test_model.py`
### TM-078: Create webhook management endpoints
**Estimate:** 30–90 minutes  
**Dependencies:** TM-077  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/api/test_webhooks.py`
### TM-079: Create webhook signing service
**Estimate:** 30–90 minutes  
**Dependencies:** TM-077  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/webhooks/test_signing.py`
### TM-080: Create webhook delivery worker
**Estimate:** 30–90 minutes  
**Dependencies:** TM-077, TM-079, TM-061  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/webhooks/test_delivery.py`
### TM-081: Create WebSocket authentication handshake
**Estimate:** 30–90 minutes  
**Dependencies:** TM-018, TM-024  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/ws/test_auth.py`
### TM-082: Create websocket notification dispatcher
**Estimate:** 30–90 minutes  
**Dependencies:** TM-081, TM-065  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/ws/test_notifications.py`
### TM-083: Create Redis pub/sub fanout adapter
**Estimate:** 30–90 minutes  
**Dependencies:** TM-082  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/ws/test_redis_fanout.py`
### TM-084: Create frontend auth session shell
**Estimate:** 30–90 minutes  
**Dependencies:** TM-020, TM-021  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `npm run test && npm run typecheck`
### TM-085: Create frontend workspace/project navigation shell
**Estimate:** 30–90 minutes  
**Dependencies:** TM-026  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `npm run test && npm run build`
### TM-086: Create frontend work item list page
**Estimate:** 30–90 minutes  
**Dependencies:** TM-039  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `npm run test && npm run build`
### TM-087: Create frontend work item detail page
**Estimate:** 30–90 minutes  
**Dependencies:** TM-038, TM-063, TM-073  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `npm run test && npm run build`
### TM-088: Create frontend work item transition control
**Estimate:** 30–90 minutes  
**Dependencies:** TM-049  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `npm run test && npm run build`
### TM-089: Create frontend board view with backend transition calls
**Estimate:** 30–90 minutes  
**Dependencies:** TM-039, TM-049  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `npm run test && npm run build`
### TM-090: Create Playwright login and work item lifecycle test
**Estimate:** 30–90 minutes  
**Dependencies:** TM-084, TM-087, TM-088  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `npx playwright test`
### TM-090A: Create workspace and project selection contracts for local frontend navigation
**Estimate:** 30–90 minutes
**Dependencies:** TM-011, TM-013, TM-015, TM-084, TM-088
**Acceptance Criteria:**
- Backend exposes a minimal workspace list contract.
- Backend exposes a minimal workspace-scoped project list contract.
- Frontend can display a workspace selector.
- Frontend can display a project selector.
- Selecting workspace and project updates local UI context.
- Empty states remain explicit.
- No login, membership, authorization inference, workspace creation, or project creation is implemented.
- The security limitation is documented: this contract is local manual-navigation enablement until membership- and RBAC-backed listing exists.
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `ruff check <changed_backend_files> && mypy <changed_backend_files> && pytest <changed_backend_tests> && npm run lint -- <changed_frontend_files> && npm run typecheck && npm run test -- <changed_frontend_tests> && npm run build`
### TM-091: Add structured logging middleware
**Estimate:** 30–90 minutes  
**Dependencies:** TM-002  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/observability/test_logging.py`
### TM-092: Add correlation id propagation
**Estimate:** 30–90 minutes  
**Dependencies:** TM-091  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/observability/test_correlation.py`
### TM-093: Add Prometheus metrics endpoint
**Estimate:** 30–90 minutes  
**Dependencies:** TM-002  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/observability/test_metrics.py`
### TM-094: Add OpenTelemetry tracing baseline
**Estimate:** 30–90 minutes  
**Dependencies:** TM-092  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/observability/test_tracing.py`
### TM-095: Add Sentry backend/frontend capture strategy
**Estimate:** 30–90 minutes  
**Dependencies:** TM-002, TM-003  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/observability && npm run build`
### TM-096: Add rate limiting middleware for auth endpoints
**Estimate:** 30–90 minutes  
**Dependencies:** TM-020  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/security/test_rate_limits.py`
### TM-097: Add dependency and secret scanning CI gate
**Estimate:** 30–90 minutes  
**Dependencies:** TM-004  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `gh workflow run validation`
### TM-098: Add docker health checks for services
**Estimate:** 30–90 minutes  
**Dependencies:** TM-004  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `docker compose up -d && docker compose ps`
### TM-099: Add CI pipeline for backend/frontend validation
**Estimate:** 30–90 minutes  
**Dependencies:** TM-002, TM-003  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `gh workflow run ci`
### TM-100: Add production readiness smoke test suite
**Estimate:** 30–90 minutes  
**Dependencies:** TM-098, TM-099  
**Acceptance Criteria:**
- The change is isolated, reviewable, and does not introduce implementation outside its scope.
- Domain boundaries are respected.
- Tests or validation evidence are included for the changed behavior.
- Documentation or contract updates are included where required.
**Validation Commands:** `pytest tests/smoke && npx playwright test smoke`
### DOC-001: Create project README and developer onboarding guide
**Estimate:** 30–90 minutes  
**Dependencies:** TM-100  
**Acceptance Criteria:**
- `README.md` is suitable for onboarding a new engineer to the TaskMaster repository.
- Implemented features completed through TM-100 are clearly distinguished from planned or future features.
- The document includes project overview, feature overview, architecture overview, technology stack, repository structure, local development setup, backend run instructions, frontend run instructions, Docker usage, testing strategy, CI/CD workflows, observability, security controls, known limitations, and future roadmap guidance.
- Setup and run instructions are executable against the repository state completed through TM-100.
- The architecture summary reflects actual implementation rather than planned-only design.
- No major implemented subsystem through TM-100 remains undocumented in `README.md`.
**Validation Commands:** `markdown lint if available && link/reference validation if available && git diff --check README.md`

## Corrective Closure Tracks
### P1C: Phase 1 Closure - Make TaskMaster actually usable
Purpose: close the gap between Phase 1 release intent and the currently mapped implementation by finishing real auth/session behavior, authenticated frontend API usage, creation flows, usable work item screens, and a local demo path. This track is corrective only and must not expand scope into Phase 2 features.

### P1C-001: Implement real login refresh logout behavior
**Estimate:** 30-90 minutes
**Dependencies:** TM-020, TM-021, TM-022, TM-024, TM-084
**Acceptance Criteria:**
- Login uses the real backend auth endpoints rather than placeholder or shell-only behavior.
- Refresh token handling renews the frontend session without forcing a full re-login during valid session continuity.
- Logout/revocation clears client session state and invalidates the server-side refresh path exposed to the client.
- Auth error handling distinguishes invalid credentials, expired session, and revoked-session behavior well enough for Phase 1 UX completion.
- No SSO, password reset, MFA, or other Phase 2+ identity features are introduced.
**Validation Commands:** `pytest tests/api/test_auth_login.py tests/api/test_auth_refresh.py tests/api/test_auth_logout.py && npm run test -- auth && npx playwright test --grep auth`

### P1C-002: Implement frontend authenticated API client
**Estimate:** 30-90 minutes
**Dependencies:** P1C-001, TM-084, TM-090A
**Acceptance Criteria:**
- Frontend API calls use a single authenticated client abstraction rather than per-page ad hoc auth handling.
- The client attaches access credentials consistently for protected backend requests.
- The client performs refresh-and-retry behavior for recoverable expired-session cases without duplicating logic across screens.
- Unauthorized and forbidden responses surface through backend-driven permission/session outcomes instead of frontend-invented workflow rules.
- The client remains scoped to Phase 1 APIs and does not add speculative SDK layers or multi-tenant abstractions beyond current needs.
**Validation Commands:** `npm run lint && npm run typecheck && npm run test -- api-client`

### P1C-003: Create organization creation endpoint and UI shell
**Estimate:** 30-90 minutes
**Dependencies:** P1C-002, TM-009, TM-013, TM-024, TM-025, TM-085
**Acceptance Criteria:**
- A backend endpoint exists to create an organization using authenticated user context and Phase 1 validation rules.
- A frontend shell exists for organization creation and submits through the authenticated API client.
- Success flow returns enough backend state for the user to continue into workspace setup without manual data manipulation.
- Validation and duplicate-name failures are displayed using backend response data.
- Scope stays limited to single-organization creation flow needed for Phase 1 onboarding.
**Validation Commands:** `pytest tests/api/test_organization_create.py && npm run test -- organization-create && npx playwright test --grep organization`

### P1C-004: Create workspace creation endpoint and UI shell
**Estimate:** 30-90 minutes
**Dependencies:** P1C-003, TM-011, TM-013, TM-024, TM-025, TM-085, TM-090A
**Acceptance Criteria:**
- A backend endpoint exists to create a workspace within an authorized organization context.
- A frontend shell exists for workspace creation and submits through the authenticated API client.
- The response updates local frontend selection/navigation context so the created workspace becomes usable immediately.
- Unauthorized organization membership or invalid parent context is rejected by backend authorization/validation rules.
- Scope excludes advanced workspace settings and remains limited to Phase 1 creation flow.
**Validation Commands:** `pytest tests/api/test_workspace_create.py && npm run test -- workspace-create && npx playwright test --grep workspace`

### P1C-005: Create project creation endpoint and UI shell
**Estimate:** 30-90 minutes
**Dependencies:** P1C-004, TM-026, TM-024, TM-025, TM-085, TM-090A
**Acceptance Criteria:**
- A backend endpoint exists to create a project within an authorized workspace context.
- A frontend shell exists for project creation and submits through the authenticated API client.
- The created project is added to the frontend navigation context without requiring hardcoded or manual selection steps.
- Backend validation handles invalid workspace scope, duplicate-name constraints, and membership authorization.
- Scope excludes Phase 2 project administration capabilities and remains limited to initial creation flow.
**Validation Commands:** `pytest tests/api/test_project_create.py && npm run test -- project-create && npx playwright test --grep project`

### P1C-006: Apply membership RBAC filtering to workspace project lists
**Estimate:** 30-90 minutes
**Dependencies:** P1C-004, P1C-005, TM-023, TM-025
**Acceptance Criteria:**
- Workspace and project list responses are filtered by effective membership/RBAC rules rather than returning unscoped data.
- Frontend list views consume only backend-filtered results and do not implement permission logic on their own.
- Unauthorized resources are omitted or denied consistently across list and selection flows.
- Tests cover positive membership visibility and negative cross-scope access cases.
- Scope excludes Phase 2 advanced role management and remains limited to Phase 1 list visibility enforcement.
**Validation Commands:** `pytest tests/rbac tests/api/test_workspace_project_visibility.py && npx playwright test --grep rbac`

### P1C-007: Wire frontend work item list to backend API
**Estimate:** 30-90 minutes
**Dependencies:** P1C-002, P1C-005, P1C-006, TM-039, TM-086, TM-090A
**Acceptance Criteria:**
- The work item list page loads real backend project-scoped data through the authenticated API client.
- Loading, empty, and error states are handled using actual backend responses.
- The selected workspace/project context drives which list data is requested.
- Frontend no longer relies on stubbed or static work item list content for the Phase 1 path.
- Scope stays limited to Phase 1 list retrieval and does not add advanced search/filter features beyond existing contracts.
**Validation Commands:** `pytest tests/api/test_work_item_list.py && npm run test -- work-item-list && npx playwright test --grep \"work item list\"`

### P1C-008: Wire frontend work item detail to backend API
**Estimate:** 30-90 minutes
**Dependencies:** P1C-002, P1C-007, TM-038, TM-087
**Acceptance Criteria:**
- The work item detail page loads real backend data for the selected item.
- Detail rendering handles missing, unauthorized, and stale selection cases using backend outcomes.
- Navigation from the real list view into detail view works without mock data.
- Frontend displays backend-provided workflow/state information rather than inventing client-side state truth.
- Scope excludes Phase 2 analytics or cross-project detail experiences.
**Validation Commands:** `pytest tests/api/test_work_item_detail.py && npm run test -- work-item-detail && npx playwright test --grep \"work item detail\"`

### P1C-009: Wire frontend board to backend workflow and work item APIs
**Estimate:** 30-90 minutes
**Dependencies:** P1C-002, P1C-007, P1C-008, TM-047, TM-048, TM-049, TM-089
**Acceptance Criteria:**
- The board loads columns and cards from backend workflow/work item data for the active project.
- Transition actions use the backend workflow transition API and reflect backend validation failures to the user.
- The frontend board no longer depends on placeholder card or status data for the Phase 1 flow.
- Workflow state ordering and move eligibility are backend-driven.
- Scope excludes realtime collaboration or advanced board customization beyond Phase 1 usability.
**Validation Commands:** `pytest tests/api/test_work_item_transition.py tests/workflow && npm run test -- board && npx playwright test --grep board`

### P1C-010: Add frontend work item create update flows
**Estimate:** 30-90 minutes
**Dependencies:** P1C-002, P1C-007, P1C-008, TM-037, TM-040
**Acceptance Criteria:**
- Users can create and update work items from the frontend against the real backend APIs.
- Forms handle backend validation errors and optimistic version conflicts in a user-visible Phase 1-safe manner.
- Successful create/update operations refresh affected list/detail views without manual page surgery.
- Create/update flows use the generic work item model already planned rather than introducing type-specific frontend forms.
- Scope excludes bulk edit, automation, and other post-Phase-1 authoring features.
**Validation Commands:** `pytest tests/api/test_work_item_create.py tests/api/test_work_item_update.py && npm run test -- work-item-form && npx playwright test --grep \"work item create|work item update\"`

### P1C-011: Add local demo seed command
**Estimate:** 30-90 minutes
**Dependencies:** P1C-001, P1C-003, P1C-004, P1C-005, P1C-009, P1C-010, DOC-001
**Acceptance Criteria:**
- A documented local command seeds a minimal Phase 1 demo environment with at least one usable user, organization, workspace, project, workflow, and representative work items.
- Seeded data is compatible with the real login and frontend flows defined in the P1C track.
- The command is safe for local/demo usage and clearly separated from production data handling assumptions.
- Developer onboarding docs identify when and how to use the demo seed path.
- Scope excludes synthetic scale/performance data generation and multi-tenant fixture complexity.
**Validation Commands:** `documented local demo seed command executes successfully && docker compose up -d && npx playwright test --grep smoke`

### P1C-012: Add Phase 1 closure acceptance E2E test
**Estimate:** 30-90 minutes
**Dependencies:** P1C-001, P1C-002, P1C-003, P1C-004, P1C-005, P1C-006, P1C-007, P1C-008, P1C-009, P1C-010, P1C-011, TM-090, TM-100
**Acceptance Criteria:**
- One end-to-end acceptance path covers real login, authenticated navigation, organization/workspace/project creation or seeded access, work item list/detail usage, board interaction, and create/update behavior.
- The test proves the Phase 1 product is usable without hidden manual setup beyond the documented seed/onboarding path.
- Failures in auth, RBAC, list/detail wiring, or board transitions are observable from this acceptance flow.
- The test is corrective to Phase 1 closure and does not expand into collaboration, integrations, or enterprise roadmap areas.
- Release-plan references are updated so this E2E path is an explicit Phase 1 closure gate.
**Validation Commands:** `docker compose up -d && documented local demo seed command && npx playwright test --grep \"phase 1 closure\"`
