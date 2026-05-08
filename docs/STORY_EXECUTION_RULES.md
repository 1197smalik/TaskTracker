# Story Execution Rules

## Source Of Truth
All story work is governed by:
- `_bmad-output/planning-artifacts/09-story-decomposition/story-map.md`
- `_bmad-output/planning-artifacts/10-dependency-graphs/execution-ordering.md`
- `_bmad-output/planning-artifacts/11-autonomous-coding-loop/codex-execution-workflow.md`

## One Story At A Time
- Implement exactly one TM story per Codex run, per task, and per branch.
- Branch naming format: `story/TM-###-short-title`.
- Do not batch multiple stories because they look related.
- Do not add speculative code for later stories.
- Do not implement adjacent stories in the same run.

## Required Pre-Implementation Check
Before editing code for a story, confirm:
- the story id and title
- story dependencies are already complete
- the relevant planning artifacts for the affected domain
- the validation commands for the story
- whether the change is backend, frontend, Docker/infrastructure, security-sensitive, or test-only

## Domain Artifact Mapping
Use these planning artifacts by default:
- Backend/domain work: `_bmad-output/planning-artifacts/04-system-architecture/backend-architecture.md`
- Frontend work: `_bmad-output/planning-artifacts/03-ux-architecture/frontend-architecture.md`
- Docker/runtime work: `_bmad-output/planning-artifacts/14-devops-and-infra/Docker-architecture.md`
- Security/auth/RBAC work: `_bmad-output/planning-artifacts/08-security-model/security-model.md` and `_bmad-output/planning-artifacts/12-validation-gates/security-validation.md`
- Validation/test expectations: `_bmad-output/planning-artifacts/12-validation-gates/` and `_bmad-output/planning-artifacts/15-testing-strategy/testing-strategy.md`

## Definition Of Done Per Story
A story is not done until all of the following are true:
- acceptance criteria are satisfied
- relevant validation commands passed
- changed behavior has tests or explicit validation evidence
- contract/doc updates were included where required
- no unrelated files were modified
- PR notes include risk and rollback assessment
- validation evidence exists before commit

## Retry Limit
- Attempt 1: implement the story directly.
- Attempt 2: fix concrete validation failures.
- Attempt 3: minimal rework based on root cause.
- After attempt 3, stop and escalate with a failure report.

## Explicit Prohibitions
- Do not bypass dependency order.
- Do not hide architecture changes inside feature stories.
- Do not introduce authorization decisions in the frontend.
- Do not change workflow state outside backend validation.
- Do not commit secrets, caches, generated artifacts, or local machine files.
