# Rollback Strategy
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Rollback Principles
Rollback must be planned before release, not after failure. Small story branches and safe migrations are the foundation.

## Application Rollback
- Keep previous deployable image/artifact.
- Use versioned environment configuration.
- Maintain compatibility with current DB schema during rollback window.

## Database Rollback
- Prefer backward-compatible migrations.
- Avoid destructive schema changes in same release as code switch.
- Use expand-and-contract migration pattern.
- Back up before high-risk migrations.

## Feature Rollback
- Use feature flags for high-risk behavior.
- Disable feature before code rollback when possible.
- Webhooks/integrations should support pause/disable state.

## Incident Rollback Decision
Rollback when:
- Authentication or RBAC is compromised.
- Data writes are corrupting state.
- Workflow transitions are invalid.
- Error rate exceeds threshold and fix is not immediate.

## Rollback Validation
After rollback:
- Health checks pass.
- Login flow works.
- Work item read/list works.
- No migration mismatch errors.
- Observability confirms error recovery.
