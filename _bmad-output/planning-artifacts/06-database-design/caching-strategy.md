# Caching Strategy
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Cache Philosophy
Cache only data that is safe to invalidate and expensive enough to justify operational complexity. Do not cache authorization decisions without strict invalidation.

## Redis Use Cases
- Rate limiting counters.
- Session/revocation metadata where needed.
- WebSocket fanout/pub-sub.
- Background job broker/result metadata.
- Short-lived workspace/project metadata caches.
- Debounced notification aggregation.

## What Not To Cache Initially
- Fine-grained permissions as long-lived cache.
- Workflow transition validation results.
- Audit logs.
- Work item writes.

## Cache Invalidation
- Project/workspace metadata cache invalidated on membership, role, or project update.
- Board view cache, if introduced later, invalidated by work_item changed events.
- Notification counts updated by event processing.

## HTTP/API Caching
- Authenticated APIs should default to no shared caching.
- Static frontend assets should be cacheable.
- ETags may be added later for heavy read endpoints.

## Tradeoff
Caching too early can create permission leaks and stale workflow behavior. Initial performance should come from correct indexes, pagination, and query design. Redis should support rate limits, jobs, and realtime first.
