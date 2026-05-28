# Backend Validation
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Required Commands
- `./.venv/bin/ruff check apps/backend/src apps/backend/tests`
- `./.venv/bin/python -m mypy apps/backend/src apps/backend/tests`
- `./.venv/bin/python -m pytest apps/backend/tests -q`
- `./.venv/bin/python -m pytest apps/backend/tests --cov`
- `cd apps/backend && ../../.venv/bin/alembic upgrade head`
- `cd apps/backend && ../../.venv/bin/alembic downgrade -1` for migration stories where feasible

## Critical Test Areas
- Authentication lifecycle.
- Refresh token rotation/revocation.
- RBAC permission evaluator.
- Tenant/workspace/project boundary checks.
- Work item CRUD invariants.
- Workflow transition validator.
- Audit writer.
- Event outbox.
- Webhook signing and retry behavior.

## Blocking Failures
- Any protected endpoint without auth test.
- Any state-changing endpoint without permission test.
- Any workflow transition bypass.
- Any migration that cannot run on clean database.
- Any audit-sensitive operation without audit test.
