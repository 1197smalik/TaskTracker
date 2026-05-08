# Testing Strategy
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Testing Pyramid
- Unit tests: domain validators, RBAC evaluator, workflow rules.
- Integration tests: API + DB behavior, transactions, audit/outbox.
- Contract tests: OpenAPI compatibility.
- E2E tests: critical user workflows through frontend.
- Performance tests: board/work item list, websocket, DB queries.
- Security tests: auth, RBAC, tenant isolation.

## Critical Backend Test Suites
- Identity/session lifecycle.
- RBAC permission matrix.
- Project/workspace boundaries.
- Work item invariants.
- Workflow transition rules.
- Audit and event outbox transactionality.
- Webhook signing and retry.

## Critical Frontend Test Suites
- Authentication flow.
- Project navigation.
- Work item creation/detail/update.
- Board transition behavior.
- Forbidden action handling.
- Notification display.

## Test Data Strategy
- Use factories/fixtures.
- Avoid brittle static global fixtures.
- Include multiple organizations/workspaces to catch boundary leaks.
- Include role permutations for RBAC tests.

## Coverage Policy
Coverage target matters most for critical domains. A high global number with poor RBAC/workflow coverage is unacceptable.
