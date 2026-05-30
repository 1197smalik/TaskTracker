# GitHub Workflows

## validation
TM-097 adds `.github/workflows/validation.yml` as the dependency and secret
scanning gate required by the planning baseline.

Trigger surface:
- `pull_request` targeting `main` or `revamp`
- `push` to `main` or `revamp`
- manual `workflow_dispatch`

Scanner contract:
- Python: `pip-audit` against the installed backend environment
- Node: `npm audit --audit-level=high` from `apps/frontend`
- Secrets: `gitleaks` using `.gitleaks.toml`

Manual run:
- `gh workflow run validation`
