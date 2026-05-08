# Production Hardening
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Production Readiness Themes
- Secure runtime configuration.
- Repeatable deployment.
- Safe migrations.
- Observable behavior.
- Rollback capability.
- Scalable architecture.
- Incident response readiness.

## Hardening Checklist

### Application
- Strict environment validation at startup.
- Debug mode disabled.
- Secure CORS configuration.
- Rate limiting enabled.
- Request size limits configured.
- Structured error handling.
- Correlation IDs propagated.

### Security
- Secrets from secret manager/environment only.
- JWT/refresh secrets rotated through controlled process.
- API tokens hashed at rest.
- Webhook secrets rotatable.
- RBAC deny-by-default.
- Audit logs enabled for sensitive actions.

### Database
- Backups scheduled and tested.
- Connection pooling configured.
- Slow query logging enabled.
- Indexes reviewed for critical endpoints.
- Migrations tested on staging copy.

### Infrastructure
- Health checks for all services.
- Resource limits for containers.
- Nginx hardened headers.
- TLS configured at edge/reverse proxy.
- Cloudflare Tunnel compatibility documented.

### Observability
- Metrics dashboards.
- Error tracking.
- Log aggregation.
- Distributed tracing.
- Alerting for critical failure modes.

## Feature Flags
Use feature flags for risky features: workflow builder changes, websocket fanout, webhooks, advanced automation, AI features.

## Blue/Green Possibility
Initial Docker Compose may use simple rolling replacement, but architecture should not block blue/green later. Kubernetes readiness should include separate deployments, readiness probes, and traffic switching strategy.
