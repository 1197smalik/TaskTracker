# Indexing Strategy
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Goals
Indexes must support fast workspace/project navigation, board loading, search filters, audit queries, and permission-scoped data access without over-indexing early.

## Core Indexes

| Table | Index | Reason |
|---|---|---|
| users | email unique | Login and invitation identity |
| memberships | user_id, organization_id, workspace_id | Permission checks |
| projects | workspace_id, key | Project lookup |
| work_items | project_id, current_state_id | Board columns |
| work_items | project_id, assignee_id, status | My work filters |
| work_items | project_id, type, priority | Common filters |
| work_items | project_id, sprint_id | Sprint board/backlog |
| comments | work_item_id, created_at | Detail page comments |
| activity_events | entity_type, entity_id, created_at | Activity timeline |
| audit_logs | organization_id, entity_type, entity_id, created_at | Audit search |
| event_outbox | status, next_attempt_at | Worker dispatch |
| notifications | recipient_id, read_at, created_at | Notification center |

## Search Strategy
Initial release can use PostgreSQL trigram/full-text search for work item title/description. Future search extraction can use OpenSearch/Meilisearch or pgvector for AI/RAG features.

## Pagination Strategy
- Use cursor pagination for activity, comments, audit logs, notifications.
- Offset pagination is acceptable only for small admin lists.
- Board loading should use state-grouped pagination or server-side batching.

## Performance Guardrails
- Every API list endpoint must declare expected indexes.
- Any query over work_items must be tenant/project scoped.
- Query plans must be reviewed for board, backlog, and audit endpoints.
- Avoid unbounded JSONB filters until indexing strategy is explicit.
