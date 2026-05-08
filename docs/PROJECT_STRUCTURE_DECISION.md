# Project Structure Decision

## Decision
TaskMaster will implement as a monorepo with separate backend, frontend, infrastructure, and documentation areas. This defines the target structure for future stories only; it does not authorize creating implementation code outside active story scope.

Primary sources:
- `_bmad-output/planning-artifacts/02-prd/prd.md`
- `_bmad-output/planning-artifacts/03-ux-architecture/frontend-architecture.md`
- `_bmad-output/planning-artifacts/04-system-architecture/backend-architecture.md`
- `_bmad-output/planning-artifacts/14-devops-and-infra/Docker-architecture.md`
- `_bmad-output/planning-artifacts/17-risk-analysis/architecture-decisions.md`

## Required Architecture Summary
- Backend: modular monolith with domain-driven boundaries.
- Frontend: React/TypeScript presentation layer with API-first contracts.
- Infrastructure: Docker Compose first, Kubernetes-ready later.
- Data and events: PostgreSQL, Redis, background worker, transactional outbox.
- Security: backend-owned auth, RBAC, audit logging, rate limiting, token controls.

## Target Repository Layout
```text
.
├── AGENTS.md
├── docs/
│   ├── IMPLEMENTATION_WORKFLOW.md
│   ├── STORY_EXECUTION_RULES.md
│   ├── VALIDATION_COMMANDS.md
│   ├── BRANCHING_STRATEGY.md
│   └── PROJECT_STRUCTURE_DECISION.md
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── application/
│   │   ├── domain/
│   │   ├── repositories/
│   │   └── infrastructure/
│   ├── migrations/
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── features/
│   │   ├── components/
│   │   ├── lib/
│   │   └── state/
│   └── tests/
├── infra/
│   ├── docker/
│   ├── nginx/
│   ├── observability/
│   └── scripts/
├── contracts/
├── .github/
└── _bmad-output/planning-artifacts/
```

## Boundary Rules
- `backend/` owns business rules, workflow validation, auth, RBAC, audit, and event dispatch behavior.
- `frontend/` owns rendering, navigation, local UI state, and backend response presentation.
- `infra/` owns Compose, container, proxy, and observability runtime configuration.
- `contracts/` is reserved for API/OpenAPI and related shared contracts.
- `docs/` holds execution policy, architecture summaries, and implementation governance.

## Constraints
- Do not split into microservices during early implementation.
- Do not create per-work-item-type subsystems.
- Do not encode authorization logic in the frontend.
- Do not bypass the workflow engine with direct status writes.
- Do not add production-Kubernetes-specific structure before the planned Docker-first baseline exists.
