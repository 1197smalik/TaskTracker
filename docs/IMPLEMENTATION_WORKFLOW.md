# Implementation Workflow

## Objective
This document defines how TaskMaster moves from planning into implementation. The repository follows the BMAD execution model: one story at a time, one branch per story, validation before merge.

## Architecture Baseline
Required implementation assumptions from the planning package:
- Product goal and release order: `_bmad-output/planning-artifacts/02-prd/prd.md`
- Frontend boundary: `_bmad-output/planning-artifacts/03-ux-architecture/frontend-architecture.md`
- Backend boundary: `_bmad-output/planning-artifacts/04-system-architecture/backend-architecture.md`
- Architecture decisions: `_bmad-output/planning-artifacts/17-risk-analysis/architecture-decisions.md`

Summary:
- Backend is a modular monolith with domain boundaries.
- Frontend is API-first and must not own authorization logic.
- Workflow transitions are always backend validated.
- Audit logging and transactional outbox are core write-path concerns.
- Initial runtime is Docker Compose with production-oriented topology.

## Workflow
1. Select the next unblocked story from `_bmad-output/planning-artifacts/09-story-decomposition/story-map.md`.
2. Confirm dependencies using `_bmad-output/planning-artifacts/10-dependency-graphs/execution-ordering.md`.
3. Create a story branch using `story/TM-###-short-title`.
4. Read only the planning artifacts relevant to that story.
5. Plan the minimum change needed to satisfy the story acceptance criteria.
6. Implement only that story.
7. Run the relevant validation commands.
8. If validation fails, fix the issue and retry up to three times.
9. Prepare a PR summary with scope, validation, risk, and rollback notes.
10. Merge only after validation passes and review approves the story scope.

## Required Task Header For Future Codex Work
Every implementation task must begin with:
- `Story:` `TM-### Title`
- `Relevant Artifacts:` exact planning artifact paths
- `Dependencies Confirmed:` `yes` or the blocking dependency
- `Validation:` exact commands to run

## Scope Control Rules
- No implementation without a story id.
- No mixed-story branches.
- No schema migration in a non-migration story unless the story explicitly requires it.
- No frontend capability inference from role names.
- No backend rule enforcement delegated to the frontend.
- No generated repository noise in commits.

## Definition Of Done
A story is complete only when:
- acceptance criteria from the story map are satisfied
- dependency order was respected
- required validations passed locally
- tests and docs were updated where needed
- risk and rollback notes were written
- the branch remains limited to one story

## Escalation Conditions
Escalate instead of guessing when:
- planning artifacts disagree
- architecture boundaries would be crossed
- validation reveals upstream design gaps
- security controls are underspecified
- the story scope would need to expand to complete the work
