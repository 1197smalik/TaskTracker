# Execution Ordering and Critical Path
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Recommended Execution Policy
Execute one story per branch. Keep branches small. Do not combine unrelated stories to save time; it reduces review quality and makes rollback harder.

## Critical Path
1. Repository and validation baseline.
2. Backend skeleton and DB migration baseline.
3. Identity/RBAC.
4. Project model.
5. Work item model.
6. Workflow model and transition validator.
7. Audit/outbox.
8. Collaboration.
9. Frontend lifecycle flow.
10. Production readiness gates.

## Post-Critical-Path Documentation
- DOC-001 should execute after TM-100 so the repository README and developer onboarding guide describe the implementation as it actually exists, not the planned target state.

## Parallelization Rules
- Parallel work is allowed only when stories do not touch the same schema/module boundaries.
- Schema migrations should be serialized unless carefully reviewed.
- API contract changes should be merged before dependent frontend stories.
- TM-090A is a bridge story for local frontend navigation and should land before frontend stories that require selected workspace/project context.
- Security-sensitive work must receive stricter review.

## Blocker Handling
A blocked story must produce one of:
- A failing test that proves the blocker.
- A design question with specific alternatives.
- A dependency update story.
- A rollback recommendation.

## Definition of Done Per Story
- Acceptance criteria met.
- Validation commands pass.
- Tests added or updated.
- API/docs updated if contract changes.
- No secrets or generated noise committed.
- PR description includes risk and rollback note.
