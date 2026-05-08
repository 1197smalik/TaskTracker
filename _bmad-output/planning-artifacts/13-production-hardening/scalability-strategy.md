# Scalability Strategy
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Scaling Assumptions
Initial target: small-to-mid engineering teams. Design must avoid obvious bottlenecks and support future horizontal scaling.

## Stateless Backend
FastAPI replicas should be stateless. Durable state belongs to PostgreSQL/object storage; ephemeral coordination belongs to Redis.

## Scaling Dimensions

| Component | Initial | Scale Path |
|---|---|---|
| API | Single container | Multiple replicas behind Nginx/K8s service |
| DB | Single PostgreSQL | Read replicas, partitioning for audit/events if needed |
| Redis | Single instance | Managed Redis/cluster for pub-sub/cache/jobs |
| Workers | Single worker | Queue-specific worker pools |
| WebSockets | Backend process | Redis fanout, dedicated realtime service later |
| Attachments | Local-compatible S3 | Managed S3-compatible storage |

## Database Scaling
- Proper tenant/project scoped indexes.
- Cursor pagination.
- Query plan review.
- Separate audit/event partitions if volume grows.
- Read replica for analytics/search-heavy reads later.

## Application Scaling
- Separate worker queues by function: notifications, webhooks, indexing.
- Avoid synchronous external calls.
- Use outbox for reliable async processing.
- Apply rate limits for expensive endpoints.

## Frontend Scaling
- Static asset caching.
- Lazy-loaded admin routes.
- Virtualized lists.
- Efficient query invalidation.

## Future Extraction Criteria
Extract a module only when at least one is true:
- Independent scaling need.
- Different reliability/SLO requirement.
- Different team ownership.
- External dependency isolation.
- Data volume makes shared runtime inefficient.
