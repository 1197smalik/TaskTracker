# Release Plan
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Release 0.1: Internal Foundation
Exit criteria:
- Docker Compose up.
- Backend/frontend health checks.
- CI baseline.
- Alembic baseline.

## Release 0.2: Identity and Project Alpha
Exit criteria:
- Login/refresh/logout.
- Organization/workspace/project creation.
- RBAC enforced.

## Release 0.3: Work Item and Workflow Alpha
Exit criteria:
- Work item lifecycle.
- Workflow states/transitions.
- Transition validation.
- Audit/event outbox.

## Release 0.4: Collaboration Beta
Exit criteria:
- Comments.
- Mentions.
- Notifications.
- Activity feed.
- Frontend usable lifecycle.

## Release 0.5: Integration Beta
Exit criteria:
- API tokens.
- Webhooks.
- WebSocket updates.
- Observability dashboards.

## Release 1.0: Production MVP
Exit criteria:
- Security validation complete.
- Performance baseline complete.
- DR restore tested.
- Smoke tests pass.
- Rollback rehearsal complete.
