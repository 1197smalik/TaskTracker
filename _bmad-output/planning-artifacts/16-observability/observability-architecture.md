# Observability Architecture
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Observability Stack
- Prometheus for metrics.
- Grafana for dashboards.
- Loki for logs.
- OpenTelemetry for traces.
- Sentry for error tracking.

## Signals

### Metrics
- Request rate, latency, error rate.
- DB query latency and connection pool usage.
- Worker queue depth and job failures.
- Webhook delivery success/failure.
- WebSocket connection count.
- Auth failures and rate-limit hits.

### Logs
Structured JSON logs with correlation_id, actor_id where safe, workspace/project scope where safe, route, status, latency, and error classification.

### Traces
Trace API requests through service layer, DB calls, outbox writes, worker dispatch, and webhook delivery where applicable.

### Errors
Sentry captures unhandled exceptions with redacted context.

## Correlation
Every request should have a correlation_id. Events, audit logs, and outbox records should carry it where applicable.
