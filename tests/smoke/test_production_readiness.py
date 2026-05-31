"""Production readiness smoke checks for existing delivery surfaces."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SRC = PROJECT_ROOT / "apps/backend/src"

if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from taskmaster_backend.app import create_app


def test_backend_health_endpoint_returns_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics_endpoint_returns_prometheus_payload() -> None:
    client = TestClient(create_app())

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "taskmaster_http_requests_total" in response.text


def test_frontend_build_completes() -> None:
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=PROJECT_ROOT / "apps/frontend",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_docker_compose_config_is_valid() -> None:
    result = subprocess.run(
        ["docker", "compose", "config"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "services:" in result.stdout
    assert "healthcheck:" in result.stdout


def test_ci_workflow_exposes_backend_and_frontend_validation_jobs() -> None:
    workflow_path = PROJECT_ROOT / ".github/workflows/ci.yml"

    assert workflow_path.exists()

    workflow_text = workflow_path.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow_text
    assert "backend-validation:" in workflow_text
    assert "frontend-validation:" in workflow_text


def test_frontend_package_declares_build_script() -> None:
    package_json = json.loads(
        (PROJECT_ROOT / "apps/frontend/package.json").read_text(encoding="utf-8")
    )

    assert package_json["scripts"]["build"]
