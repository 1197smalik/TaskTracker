# Epic Dependency Graph
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

```mermaid
flowchart TD
  E1[Platform Foundation] --> E2[Identity and RBAC]
  E1 --> E3[Project Planning]
  E2 --> E3
  E3 --> E4[Work Items]
  E3 --> E5[Workflow Engine]
  E4 --> E5
  E4 --> E6[Audit and Events]
  E5 --> E6
  E4 --> E7[Collaboration and Notifications]
  E6 --> E8[Integrations]
  E6 --> E9[Realtime]
  E2 --> E10[Frontend Experience]
  E3 --> E10
  E4 --> E10
  E5 --> E10
  E1 --> E11[Production Readiness]
  E6 --> E11
  E8 --> E11
  E9 --> E11
```

## Critical Path
Platform Foundation -> Identity/RBAC -> Project -> Work Item -> Workflow Engine -> Audit/Event Outbox -> Collaboration/Realtime/Integrations -> Production Readiness.

## Parallelization Opportunities
- Frontend shell can begin after API contracts and auth contracts are stable.
- Project metadata models can run in parallel after project foundation.
- Audit model and event outbox can be built while collaboration model starts, after work item baseline.
- Observability middleware can begin early after backend skeleton.

## Blockers
- Work item transition endpoint depends on workflow validator.
- Board UI depends on work item list and transition APIs.
- Webhooks depend on event outbox.
- Notifications depend on comments/mentions and event dispatch.
- Production readiness depends on health checks, CI, observability, security gates.
