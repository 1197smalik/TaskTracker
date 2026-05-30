# Docker Infrastructure

TM-098 adds explicit Docker health checks for the local TaskMaster stack.

## Health checks
- `backend`: HTTP probe to `http://127.0.0.1:8000/api/v1/health`
- `frontend`: HTTP probe to `http://127.0.0.1:5173`
- `postgres`: `pg_isready`
- `redis`: `redis-cli ping`
- `nginx`: HTTP probe to `http://127.0.0.1/`

All service definitions use explicit `interval`, `timeout`, `retries`, and
`start_period` values in `docker-compose.yml`.

## Validation
- `docker compose config`
- `docker compose up -d && docker compose ps`
