# Local Docker Development

This repository includes a local Docker Compose baseline for `TM-004`.

## Included Services
- backend
- frontend
- postgres
- redis
- nginx

## Files
- `docker-compose.yml`
- `apps/backend/Dockerfile`
- `apps/frontend/Dockerfile`
- `infra/nginx/nginx.conf`
- `.env.example`

## Startup
1. Copy `.env.example` to `.env` if you want to override defaults.
2. Run `docker compose config` to validate the configuration.
3. Run `docker compose build` to build local images.
4. Run `docker compose up` to start the baseline stack.

## Default Ports
- Nginx: `8080`
- Frontend dev server: `5173`
- Backend app: `8000`
- PostgreSQL: `5432`
- Redis: `6379`

## Notes
- This is a local-development baseline, not a production deployment.
- No secrets are committed; `.env.example` contains non-secret development defaults only.
- The stack remains compatible with later Kubernetes-oriented deployment work.
- TM-005 database lifecycle work is intentionally deferred. PostgreSQL is provisioned only as a runtime dependency.
