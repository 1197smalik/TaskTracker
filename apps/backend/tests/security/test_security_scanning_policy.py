"""Static checks for the CI security scanning policy contract."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
POLICY_PATH = REPO_ROOT / "docs" / "SECURITY_SCANNING_POLICY.md"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


def _policy_text() -> str:
    return POLICY_PATH.read_text(encoding="utf-8")


def test_security_scanning_policy_document_exists() -> None:
    assert POLICY_PATH.exists()


def test_scanner_choices_are_explicit() -> None:
    policy = _policy_text()

    assert "Python dependencies | `pip-audit`" in policy
    assert "Node dependencies | `npm audit`" in policy
    assert "`npm audit --audit-level=high`" in policy
    assert "Secrets | `gitleaks`" in policy
    assert "`gitleaks detect`" in policy


def test_failure_thresholds_are_stable() -> None:
    policy = _policy_text()

    assert "Python dependencies | Fail on high or critical vulnerabilities." in policy
    assert "Node dependencies | Fail on high or critical vulnerabilities." in policy
    assert "Moderate advisories do not fail the gate" in policy
    assert "Secrets | Fail on any verified or high-confidence secret finding." in policy


def test_allowlist_policy_requires_reason_and_review_date() -> None:
    policy = _policy_text()

    assert "explicit file-based allowlist" in policy
    assert "finding identifier or fingerprint" in policy
    assert "reason" in policy
    assert "owner" in policy
    assert "expiry or review date" in policy
    assert "Blanket allowlists are forbidden" in policy


def test_workflow_trigger_policy_is_stable() -> None:
    policy = _policy_text()

    assert "`pull_request` targeting `main` or `revamp`" in policy
    assert "`push` to `main` or `revamp`" in policy
    assert "manual `workflow_dispatch`" in policy
    assert "workflow name must be `validation`" in policy
    assert "`gh workflow run validation`" in policy


def test_tm097_validation_workflow_is_not_implemented_yet() -> None:
    validation_workflows = [
        path
        for path in WORKFLOWS_DIR.glob("validation.*")
        if path.suffix in {".yml", ".yaml"}
    ]

    assert validation_workflows == []

