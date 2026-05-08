# Branching Strategy

## Model
TaskMaster uses trunk-based development with short-lived story branches.

Primary source:
- `_bmad-output/planning-artifacts/11-autonomous-coding-loop/branching-and-pr-strategy.md`
- `_bmad-output/planning-artifacts/11-autonomous-coding-loop/codex-execution-workflow.md`

## Branch Naming
Use:
```text
story/TM-###-short-title
```

Examples:
- `story/TM-001-repository-boundary-checklist`
- `story/TM-004-docker-compose-baseline`

## Rules
- One story per branch.
- Main must remain mergeable and deployable.
- Do not combine unrelated fixes into a story branch.
- Keep commits small and reference the story id.
- Keep schema and contract changes tightly coupled to the story that requires them.

## Pull Request Requirements
Every PR must include:
- story id and title
- relevant planning artifacts consulted
- dependency confirmation
- scope summary
- files changed by area
- validation commands run and results
- tests added or updated
- risk assessment
- rollback note

## Review Ownership
Use stricter review when applicable:
- security-sensitive changes: security review
- workflow engine changes: backend/domain review
- schema migrations: platform/backend review
- frontend user flow changes: UX/frontend review
- CI or infrastructure changes: DevOps review

## Merge Blocks
Do not merge when:
- validation fails
- the branch includes multiple stories
- scope expanded beyond the active story without approval
- protected endpoint changes lack auth or RBAC coverage
- repository noise or generated artifacts are included
