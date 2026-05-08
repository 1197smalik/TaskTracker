# Performance Testing
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Performance Targets
- Authenticated API basic reads: p95 under 300ms for normal load.
- Work item list filtered by project/state: p95 under 500ms for realistic project sizes.
- Board initial load: p95 under 1.5s with pagination/lazy loading.
- Transition endpoint: p95 under 500ms excluding external async side effects.
- WebSocket event fanout: under 1s for normal workspace volume.

## Test Scenarios
- Project with 5,000 work items.
- Sprint with 500 active items.
- Board with 8 workflow states.
- 100 concurrent users reading board/list endpoints.
- 50 concurrent users transitioning items.
- 1,000 websocket connections in staged environment before scale claims.

## Database Performance
- Explain analyze for work item list, board, audit log query.
- Verify index usage.
- Check slow query logs.
- Test pagination boundaries.

## Load Test Exit Criteria
No release should claim production readiness if critical path endpoints degrade unpredictably under expected small-team load.
