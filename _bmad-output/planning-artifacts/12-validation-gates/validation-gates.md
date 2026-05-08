# Validation Gates
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Gate Philosophy
Validation is not a final step; it is an execution boundary. A story is incomplete until the relevant gates pass.

## Backend Gates
- Ruff formatting/linting.
- MyPy type checking.
- pytest unit tests.
- pytest integration tests for API and DB behavior.
- Coverage threshold for critical domains.
- Migration upgrade/downgrade validation.
- Security-focused tests for auth/RBAC.

## Frontend Gates
- ESLint.
- TypeScript type checking.
- Unit/component tests.
- Playwright critical flows.
- Production build validation.
- Accessibility smoke checks for core forms.

## Infrastructure Gates
- Docker Compose config validation.
- Container build validation.
- Health check validation.
- Nginx config validation.
- Environment variable completeness check.

## Security Gates
- Dependency scanning.
- Secret scanning.
- Auth flow tests.
- RBAC boundary tests.
- API token scope tests.
- WebSocket authorization tests.
- OWASP baseline checklist.

## Performance Gates
- Board list query performance test.
- Work item filter query performance test.
- WebSocket concurrent connection test.
- Background worker throughput smoke test.
- DB index/query plan review for high-volume endpoints.

## Release Gate
A release candidate must pass:
- Full CI.
- Smoke test suite.
- Migration dry run.
- Rollback rehearsal for the release.
- Observability dashboard check.
- Security checklist signoff.
