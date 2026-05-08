# Branching and PR Strategy
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Branch Model
Use trunk-based development with short-lived story branches. The main branch must always be deployable.

## Branch Naming
`story/TM-###-short-title`

Examples:
- `story/TM-018-jwt-access-token-utility`
- `story/TM-049-work-item-transition-endpoint`

## Commit Policy
- Prefer small commits grouped by logical change.
- Commit messages reference story id.
- Avoid noisy formatting-only commits unless they are the story.

## PR Size Control
A PR should normally touch one domain/module. If a story requires migration, endpoint, service, and test updates, that is acceptable only when all are necessary for the same story.

## Required PR Checks
- Backend lint/type/test where backend changed.
- Frontend lint/type/build/test where frontend changed.
- Migration validation where schema changed.
- Security checks where dependencies or auth changed.
- Smoke checks for critical path changes.

## Review Ownership
- Security-sensitive changes: security architect review.
- Workflow engine changes: backend/domain architect review.
- Migrations: platform/backend review.
- Frontend UX flows: UX review.
- CI/CD/infrastructure: DevOps review.
