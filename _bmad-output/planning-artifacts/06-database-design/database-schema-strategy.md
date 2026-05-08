# Database Schema Strategy
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Database Choice
PostgreSQL is the source of truth. It supports relational integrity, transactional consistency, JSONB for selective extensibility, strong indexing, row-level constraints, and future analytics/search integration.

## Schema Strategy
Use explicit tables for stable core entities and JSONB only for controlled extension fields. Avoid making the entire domain schema dynamic.

## Major Table Groups

### Identity
- users
- organizations
- workspaces
- memberships
- roles
- permissions
- role_permissions
- sessions
- api_tokens

### Project
- projects
- boards
- board_columns
- sprints
- milestones
- epics
- labels
- components
- versions

### Work Item
- work_items
- work_item_links
- work_item_labels
- work_item_components
- work_item_versions
- work_item_watchers

### Workflow
- workflow_definitions
- workflow_states
- workflow_transitions
- workflow_transition_rules
- workflow_assignments

### Collaboration
- comments
- mentions
- attachments
- notifications
- activity_events
- reactions

### Audit and Events
- audit_logs
- entity_versions
- security_events
- event_outbox
- webhook_deliveries

## Migration Strategy
- Alembic is the only approved schema migration mechanism.
- Every schema change must include forward migration and rollback assessment.
- Destructive migrations require two-phase rollout: add new schema, backfill, switch reads/writes, remove old schema later.
- Large backfills should run as background jobs or maintenance scripts, not blocking migrations.

## Multi-Tenancy Strategy
Initial release uses shared database, shared schema, tenant scoping via organization_id/workspace_id. This is simpler and appropriate early. Future enterprise isolation can support dedicated database or schema per enterprise customer if needed.

## Data Retention
- Audit logs: long retention, configurable later.
- Activity feed: medium-to-long retention.
- Webhook delivery logs: limited retention with summarized failure counts.
- Sessions: expire aggressively.
- Deleted entities: soft delete for business entities where audit/history matters.

## Consistency Rules
- Use database constraints for required relationships.
- Use application services for cross-domain business invariants.
- Use optimistic concurrency/version columns for high-conflict entities such as work items and workflow definitions.
