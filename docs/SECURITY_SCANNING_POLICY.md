# Security Scanning Policy

## Scope
This document defines the TM-097 dependency and secret scanning contract. It is
policy only: TM-097 owns the GitHub Actions workflow implementation.

## Scanner Contract
| Area | Scanner | Command Contract |
|---|---|---|
| Python dependencies | `pip-audit` | `pip-audit` over the repository root virtual environment or generated requirements input |
| Node dependencies | `npm audit` | `npm audit --audit-level=high` from `apps/frontend` |
| Secrets | `gitleaks` | `gitleaks detect` over the repository |

Scanner choices are intentionally explicit:
- `pip-audit` is the Python dependency scanner because it audits installed or locked Python packages against Python vulnerability databases.
- `npm audit --audit-level=high` is the Node dependency scanner because the frontend uses npm lockfiles and current moderate advisories must not fail TM-097.
- `gitleaks` is the secret scanner because it is designed for repository secret detection and CI execution.

## Failure Thresholds
| Area | CI Failure Threshold |
|---|---|
| Python dependencies | Fail on high or critical vulnerabilities. |
| Node dependencies | Fail on high or critical vulnerabilities. Moderate advisories do not fail the gate unless this policy is changed later. |
| Secrets | Fail on any verified or high-confidence secret finding. |

The current frontend package baseline has known moderate Node advisories. Those
moderate advisories are explicitly non-blocking for TM-097 and must not be
converted into silent allowlist entries.

## Allowlist Policy
Allowlists are permitted only through an explicit file-based allowlist consumed
by the scanner workflow.

Every allowlisted item must include:
- scanner name
- finding identifier or fingerprint
- affected path or dependency
- reason
- owner
- expiry or review date

Blanket allowlists are forbidden. Pattern-only allowlists that suppress whole
directories, dependency ecosystems, or secret categories are forbidden unless a
future approved story updates this policy.

## Workflow Trigger Policy
The TM-097 validation workflow must run on:
- `pull_request` targeting `main` or `revamp`
- `push` to `main` or `revamp`
- manual `workflow_dispatch`

The workflow name must be `validation` so it can satisfy the story-map command:
`gh workflow run validation`.

## Initial Implementation Boundary
TM-097 may install and execute scanners in CI, but this policy does not permit:
- dependency upgrades
- vulnerability fixes
- generated secret baselines
- blanket allowlists
- Docker or container image scanning
- product code changes

