# Event-Driven Architecture
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Objective
TaskMaster must be event-ready from day zero so collaboration, notifications, audit, webhooks, automations, analytics, and future AI systems can consume reliable domain changes.

## Event Categories

| Category | Examples |
|---|---|
| Identity Events | user.created, membership.added, role.changed |
| Project Events | project.created, sprint.started, milestone.updated |
| Work Item Events | work_item.created, assigned, transitioned, commented, linked |
| Workflow Events | workflow.definition.updated, transition.executed |
| Collaboration Events | mention.created, attachment.added, reaction.added |
| Security Events | login.failed, api_token.created, permission.denied |
| Integration Events | webhook.delivery.failed, external_git_event.received |

## Outbox Pattern
State changes and event creation must be atomic. The backend writes business state and an outbox record in the same database transaction. Background workers dispatch outbox events to websocket fanout, notifications, webhooks, and future analytics pipelines.

## Event Contract Requirements
Each event must include:
- event_id
- event_type
- occurred_at
- actor_id where applicable
- organization_id
- workspace_id
- project_id where applicable
- entity_type
- entity_id
- correlation_id
- payload version
- redacted payload body

## Delivery Semantics
- Internal processing: at-least-once.
- Webhook delivery: at-least-once with idempotency key.
- WebSocket delivery: best-effort realtime with REST reconciliation.
- Audit: durable and queryable, not dependent on event delivery.

## Failure Handling
- Outbox event retries with exponential backoff.
- Poison events move to dead-letter state after retry threshold.
- Webhook delivery failures are visible in integration admin.
- Event consumers must be idempotent.

## Future Evolution
Outbox can later publish to Kafka, NATS, or managed cloud pub/sub. The domain event contract should remain stable so extraction does not rewrite business logic.
