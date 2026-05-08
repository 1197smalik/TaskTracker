# Audit Logging Strategy
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Purpose
Audit logging provides compliance, debugging, and security investigation capability. It is separate from user-facing activity feeds.

## Audit Event Requirements
Each audit event must include:
- audit_id
- actor_id / actor_type
- organization_id
- workspace_id where applicable
- project_id where applicable
- entity_type
- entity_id
- action
- before/after summary or diff reference
- ip/user_agent where applicable
- correlation_id
- created_at

## Events To Audit
- Role and membership changes.
- Authentication/security events.
- API token lifecycle.
- Workflow definition updates.
- Work item state transitions.
- Work item deletion/restore.
- Webhook secret rotation.
- Permission denied for sensitive actions.

## Storage Strategy
Audit logs are append-only at application level. Direct modification is prohibited except controlled retention/admin operations.

## Query Strategy
Audit search must support actor, entity, action, time range, workspace/project scope.

## Redaction
Audit logs should not store secrets or full sensitive attachment content. Store metadata and change summaries.

## Tradeoff
Full diff storage is useful but can grow quickly. Initial release should store structured before/after summary for important fields and entity version references for deeper history.
