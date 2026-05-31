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

## Corrective Phase 1 Closure Track
- P1C is a corrective execution track governed by DOC-001 planning follow-up. It closes Phase 1 usability gaps that remain after the mapped TM stories and documentation baseline.
- Execute P1C only after TM-100 and DOC-001.
- Recommended sequence:
  1. P1C-001 real auth/session behavior
  2. P1C-002 authenticated frontend API client
  3. P1C-003 organization creation flow
  4. P1C-004 workspace creation flow
  5. P1C-005 project creation flow
  6. P1C-006 membership RBAC filtering on workspace/project lists
  7. P1C-007 work item list API wiring
  8. P1C-008 work item detail API wiring
  9. P1C-009 board workflow/API wiring
  10. P1C-010 work item create/update flows
  11. P1C-011 local demo seed command
  12. P1C-012 Phase 1 closure acceptance E2E test
- P1C stories remain within Phase 1 closure only. They must not pull collaboration, integrations, SSO, advanced workflow administration, or other Phase 2+ scope into the branch.
- P1C-011 should not land before the core P1C flows it demonstrates, or the seed path will freeze around placeholders instead of real behavior.
- P1C-012 is the closure gate for Phase 1 usability and should be treated as a release-blocking story for the corrected Phase 1 plan.

## Parallelization Rules
- Parallel work is allowed only when stories do not touch the same schema/module boundaries.
- Schema migrations should be serialized unless carefully reviewed.
- API contract changes should be merged before dependent frontend stories.
- TM-090A is a bridge story for local frontend navigation and should land before frontend stories that require selected workspace/project context.
- Within P1C, auth/session and API-client stories must merge before frontend wiring stories, and creation-flow endpoints must merge before seed or acceptance-test work.
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
