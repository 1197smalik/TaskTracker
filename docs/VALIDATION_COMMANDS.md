# Validation Commands

## Purpose
Validation is a merge gate, not a cleanup step. Run only the commands relevant to the story, plus any broader gates required by the changed area.

## Documentation Validation
When `make validate-docs` does not exist, use the repository docs checks below.

Commands:
```bash
find docs -type f | sort
test -f docs/PLANNING_TO_IMPLEMENTATION_BOUNDARY.md
test -f docs/STORY_EXECUTION_RULES.md
test -f docs/MODEL_SELECTION_POLICY.md
test -f docs/VALIDATION_COMMANDS.md
git diff --check
```

## Baseline Story Controls
- Story acceptance and validation source: `_bmad-output/planning-artifacts/09-story-decomposition/story-map.md`
- Global gate source: `_bmad-output/planning-artifacts/12-validation-gates/validation-gates.md`

Blocking documentation failures:
- missing required governance file
- execution rules that allow multi-story runs
- validation categories omitted for a changed control document
- repository-control change that quietly introduces implementation files

## Backend Gates
Source:
- `_bmad-output/planning-artifacts/12-validation-gates/backend-validation.md`

Commands:
```bash
ruff check .
mypy .
pytest
pytest --cov
alembic upgrade head
alembic downgrade -1
```

Use `alembic downgrade -1` for migration stories where feasible.

Blocking backend failures:
- protected endpoint without auth test
- state-changing endpoint without permission test
- workflow transition bypass
- migration that fails on a clean database
- audit-sensitive operation without audit coverage

## Frontend Gates
Source:
- `_bmad-output/planning-artifacts/12-validation-gates/frontend-validation.md`

Commands:
```bash
npm run lint
npm run typecheck
npm run test
npm run build
npx playwright test
```

Blocking frontend failures:
- local authorization inference from role names
- unhandled `403`, `409`, or `422` mutation states
- drag/drop or transition UI that assumes backend success
- API contract type errors
- broken production build

## Docker And Infrastructure Gates
Source:
- `_bmad-output/planning-artifacts/12-validation-gates/validation-gates.md`
- `_bmad-output/planning-artifacts/14-devops-and-infra/Docker-architecture.md`

Commands:
```bash
docker compose config
docker compose build
```

Required checks:
- health checks defined for core services
- environment variable completeness reviewed
- reverse proxy and websocket routing validated
- no secrets baked into images

## Security Gates
Source:
- `_bmad-output/planning-artifacts/12-validation-gates/security-validation.md`

Required checks:
- dependency vulnerability scan
- secret scan
- auth flow tests
- RBAC boundary tests
- API token scope tests
- WebSocket authorization tests
- OWASP baseline checklist review

Representative abuse cases to validate:
- cross-workspace access by id returns `403` or `404`
- invalid transition is denied with a reason
- revoked refresh token reuse is rejected
- out-of-scope API token access is denied
- unauthorized websocket subscription is blocked

## Test Strategy Gates
Source:
- `_bmad-output/planning-artifacts/15-testing-strategy/testing-strategy.md`

Required coverage focus:
- identity/session lifecycle
- RBAC permission matrix
- project and workspace boundaries
- work item invariants
- workflow transition rules
- audit and outbox transactionality
- webhook signing and retry
- frontend lifecycle and forbidden-action handling

## Release Gate
Before release work merges, confirm:
- full CI passes
- smoke tests pass
- migration dry run succeeds
- rollback rehearsal exists
- observability checks are complete
- security checklist is signed off
