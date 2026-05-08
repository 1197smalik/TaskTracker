# Implementation Readiness Checklist
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Before First Code Story
- [ ] Planning artifacts reviewed.
- [ ] Repository branch protection planned.
- [ ] CI baseline agreed.
- [ ] Docker Compose target agreed.
- [ ] Environment variable policy agreed.
- [ ] Secrets handling policy agreed.
- [ ] Story execution prompt approved.

## Before Feature Development
- [ ] Backend skeleton exists.
- [ ] Frontend skeleton exists.
- [ ] Database migrations run.
- [ ] CI validates backend and frontend.
- [ ] Docker environment boots.

## Before Production MVP
- [ ] RBAC abuse tests pass.
- [ ] Workflow transition tests pass.
- [ ] Audit logs verified.
- [ ] Event outbox verified.
- [ ] Webhook signing verified.
- [ ] WebSocket permission filtering verified.
- [ ] Backup and restore tested.
- [ ] Rollback rehearsal completed.
- [ ] Smoke tests pass.
- [ ] Observability dashboards active.
