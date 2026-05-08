# OpenAPI Standards
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Purpose
OpenAPI is the source of truth for API consumers, frontend typing, test generation, and external integration documentation.

## Standards
- Each endpoint must have summary, description, tags, request body schema, response schemas, error schemas, and auth requirements.
- Schemas must be stable and versioned through API versioning.
- Internal-only endpoints must be clearly marked or separated.
- Examples must be realistic and not contain secrets.

## Schema Naming
- `UserResponse`, `WorkspaceResponse`, `ProjectResponse`.
- `WorkItemCreateRequest`, `WorkItemUpdateRequest`, `WorkItemResponse`.
- `WorkflowTransitionRequest`, `WorkflowTransitionResponse`.
- `ApiErrorResponse`.

## Contract Review Checklist
- Is the endpoint tenant-scoped?
- Are permissions documented?
- Are validation failures documented?
- Does it leak internal IDs or sensitive fields?
- Is pagination defined?
- Does it need idempotency?
- Does it trigger events/audit logs?

## Versioning Policy
Breaking changes require new API version. Non-breaking additive changes may remain in v1. Deprecations must include documented migration path.
