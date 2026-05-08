# TaskMaster Backend

This directory contains the TaskMaster backend skeleton for `TM-002`.

Current scope:
- Python project configuration
- FastAPI application boundary
- Minimal health endpoint under `/api/v1/health`
- SQLAlchemy base metadata and session lifecycle
- Alembic baseline configuration
- Test, Ruff, and MyPy configuration

Out of scope:
- authentication and RBAC
- business services
- domain models

Migration commands:
- `./.venv/bin/python -m alembic current`
- `./.venv/bin/python -m alembic upgrade head`
- `./.venv/bin/python -m alembic downgrade base`

Alembic scripts live under `migrations/` to avoid colliding with the installed `alembic` Python package.
