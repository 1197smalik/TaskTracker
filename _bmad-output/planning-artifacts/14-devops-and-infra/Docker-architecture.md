# Docker Architecture
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Initial Services
- frontend
- backend
- postgres
- redis
- worker
- nginx
- prometheus
- grafana
- loki/promtail where feasible

## Docker Compose Use
Docker Compose is the initial development and deployment runtime. It should model production topology without pretending to be Kubernetes.

## Container Rules
- One process responsibility per container where practical.
- Health checks for backend, frontend/nginx, postgres, redis, workers.
- No secrets baked into images.
- Non-root containers where practical.
- Persistent volumes only for database and observability/storage state.

## Nginx Role
- Route frontend static app.
- Reverse proxy `/api` to backend.
- Reverse proxy websocket paths with upgrade headers.
- Apply request size limits and secure headers.

## Cloudflare Tunnel Compatibility
Cloudflare Tunnel can point to local Nginx. The app must work behind reverse proxy headers and support configured public host/origin settings.
