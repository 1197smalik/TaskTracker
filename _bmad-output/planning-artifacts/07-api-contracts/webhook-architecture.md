# Webhook Architecture
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Purpose
Webhooks allow external systems to react to TaskMaster events such as work item creation, transitions, comments, incidents, and workflow changes.

## Subscription Model
Webhook endpoints are scoped to organization/workspace. Subscriptions choose event types and optionally project filters.

## Delivery Contract
Each delivery includes:
- webhook_id
- delivery_id
- event_id
- event_type
- occurred_at
- payload_version
- signature
- payload

## Security
- HMAC signatures for every delivery.
- Secrets are generated and rotated.
- Delivery logs do not store secrets.
- Sensitive payload fields are redacted according to event type and subscriber scope.

## Retry Policy
- Exponential backoff.
- Maximum retry window defined by operational policy.
- Failed deliveries visible in admin UI.
- Dead-letter state after retry exhaustion.

## Idempotency
Consumers must use delivery_id or event_id to deduplicate. TaskMaster guarantees at-least-once delivery, not exactly-once delivery.

## Initial Event Types
- work_item.created
- work_item.updated
- work_item.transitioned
- comment.created
- mention.created
- sprint.started
- sprint.completed
- incident.created
- workflow.transition.executed

## Operational Considerations
Webhook delivery must run in background workers. External endpoint latency must never block user-facing transactions.
