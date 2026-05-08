# CI/CD Strategy
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## CI Goals
- Prevent unsafe code from reaching main.
- Validate backend, frontend, database migrations, Docker builds, and security gates.
- Keep main branch deployable.

## CI Pipeline Stages
1. Checkout and dependency setup.
2. Backend lint/type/tests.
3. Frontend lint/type/tests/build.
4. Migration validation.
5. Docker build/config validation.
6. Security scans.
7. Smoke tests where environment available.

## CD Strategy
Initial deployment can use GitHub Actions to a Docker Compose host. The deployment must:
- Pull latest approved commit.
- Validate environment configuration.
- Run migrations safely.
- Start/restart services.
- Run health checks.
- Run smoke tests.
- Roll back if health checks fail.

## Branch Protection
- Require PR reviews.
- Require CI checks.
- Block direct pushes to main.
- Require migration review for DB changes.

## Environment Promotion
- local -> dev -> staging -> production.
- Production deploys only from tagged or approved main commits.

## Secrets
CI secrets must live in GitHub environment secrets or a proper secret manager. Secrets must never be committed or printed.
