# Risk Register
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

| Risk | Severity | Probability | Mitigation |
|---|---:|---:|---|
| Scope creep into Jira clone | High | High | Strict release scope and story map control |
| Workflow engine overengineering | High | Medium | Start with structured rule types only |
| Broken RBAC causes data leak | Critical | Medium | Central evaluator and abuse tests |
| Poor DB indexing makes board slow | High | Medium | Index strategy and performance tests |
| Audit/event inconsistency | High | Medium | Transactional audit/outbox pattern |
| WebSocket scaling issues | Medium | Medium | Redis fanout and REST reconciliation |
| AI features distract from core | Medium | High | Defer AI to roadmap after stable foundation |
| Migration failure in production | High | Medium | Expand-contract migrations and rollback rehearsal |
| Integration webhooks become unreliable | Medium | Medium | Retry, dead-letter, visibility |
| Frontend duplicates business logic | High | Medium | Backend capabilities contract and review checks |

## Highest Priority Risks
1. Tenant/RBAC boundary failures.
2. Workflow transition correctness.
3. Over-scoping before core product reliability.
4. Database performance on board/list endpoints.
5. Unsafe migrations.
