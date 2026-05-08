# Architecture Decision Records
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## ADR-001: Modular Monolith First
**Decision:** Start as modular monolith.  
**Rationale:** Preserves consistency and delivery speed while maintaining clear domain boundaries.  
**Tradeoff:** Requires discipline to prevent module coupling.  
**Future:** Extract services only when scale/team boundaries justify it.

## ADR-002: Generic Work Item Abstraction
**Decision:** Model task, bug, story, incident, and subtask as typed work items.  
**Rationale:** Avoid duplicate lifecycle and collaboration logic.  
**Tradeoff:** Requires carefully designed metadata and validation.

## ADR-003: Workflow Engine as Core Domain
**Decision:** Workflow definitions/states/transitions/rules are first-class.  
**Rationale:** Differentiates TaskMaster from CRUD task apps and supports enterprise process control.  
**Tradeoff:** Adds upfront complexity.

## ADR-004: Outbox Pattern for Events
**Decision:** Use transactional outbox for domain events.  
**Rationale:** Reliable event processing without distributed transactions.  
**Tradeoff:** Requires worker and retry management.

## ADR-005: Backend-Owned Authorization
**Decision:** Backend owns all authorization decisions.  
**Rationale:** Prevents frontend bypass and supports API-first clients.  
**Tradeoff:** Frontend must depend on capability responses.

## ADR-006: Docker Compose First, Kubernetes Ready
**Decision:** Use Docker Compose initially but design for K8s.  
**Rationale:** Faster local/demo deployment, avoids premature ops overhead.  
**Tradeoff:** Some production scale patterns deferred.
