# Backend Architecture
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Architectural Style
TaskMaster starts as a modular monolith with domain-driven boundaries. This is the correct first architecture because it preserves transactional consistency, simplifies early development, and avoids premature distributed-system overhead while still allowing future microservice extraction.

## Backend Responsibilities
The backend owns:
- Authentication and session validation.
- Authorization and permission checks.
- Workflow transition validation.
- Business rules and invariants.
- Audit logging and entity change history.
- Event creation and dispatch.
- API contracts and external integration behavior.

## Logical Modules

| Module | Core Responsibility |
|---|---|
| Identity | users, orgs, workspaces, roles, permissions, sessions, API tokens |
| Project | projects, boards, sprints, milestones, epics, labels, components, versions |
| Work Item | generic work-item abstraction, hierarchy, metadata, lifecycle |
| Workflow Engine | workflow definitions, states, transitions, guards, automation triggers |
| Collaboration | comments, mentions, attachments, notifications, reactions, activity feed |
| Audit | audit log, security events, entity versioning |
| Integration | webhooks, external events, API token access, future Git integrations |
| Platform | health, observability, config, rate limits, background jobs |

## Layering

1. API layer: FastAPI routers, request/response schemas, auth dependency injection.
2. Application service layer: use-case orchestration, transactions, event emission.
3. Domain layer: domain policies, validators, invariants, domain events.
4. Repository layer: SQLAlchemy persistence and query objects.
5. Infrastructure layer: Redis, object storage, email/notification providers, metrics.

## Transaction Strategy
- Commands that change business state run in explicit database transactions.
- Audit entries are written in the same transaction as the domain change where possible.
- Outbox events are persisted transactionally before async dispatch.
- External webhooks must never be called inside the domain transaction.

## Eventing Strategy
Use internal domain events plus an outbox table. Initial dispatch can be handled by background workers. Later, outbox can feed a broker such as Kafka/NATS without changing domain code.

## API Design
- REST for core CRUD/use-case operations.
- WebSockets for realtime notifications and collaboration updates.
- Webhooks for external systems.
- API versioning begins at `/api/v1`.

## Scalability Path

### Phase 1
Single backend service, PostgreSQL, Redis, Celery/RQ, object storage, Nginx.

### Phase 2
Multiple backend replicas, Redis shared cache, background worker replicas, WebSocket scaling with Redis pub/sub.

### Phase 3
Extract high-volume domains if needed: notifications, integrations/webhooks, audit/event pipeline, search/indexing.

## Critical Design Decisions
- Generic work-item model avoids type-specific duplication.
- Workflow engine is separate from work item CRUD to prevent status logic from spreading.
- Audit is not optional middleware only; it is part of application service workflows.
- Webhook dispatch uses outbox/retry to prevent external dependency failures from breaking core writes.
