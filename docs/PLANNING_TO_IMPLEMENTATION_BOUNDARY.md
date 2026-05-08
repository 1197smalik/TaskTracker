# Planning To Implementation Boundary

Current story: `TM-001`

## Source Of Truth
The BMAD planning package under `_bmad-output/planning-artifacts/` is the source of truth for TaskMaster planning, execution ordering, validation, and readiness.

## Boundary Checklist
Use this checklist before a planning artifact becomes implementation work:

- [ ] Identify exactly one `TM-###` story.
- [ ] Confirm the story exists in `_bmad-output/planning-artifacts/09-story-decomposition/story-map.md`.
- [ ] Confirm dependencies in `_bmad-output/planning-artifacts/10-dependency-graphs/execution-ordering.md`.
- [ ] Read the relevant execution prompt in `_bmad-output/planning-artifacts/11-autonomous-coding-loop/ai-execution-prompts.md`.
- [ ] Confirm the applicable validation gates in `_bmad-output/planning-artifacts/12-validation-gates/validation-gates.md`.
- [ ] Confirm readiness constraints in `_bmad-output/planning-artifacts/19-implementation-readiness/readiness-checklist.md`.
- [ ] Decide the minimum story scope and exclude adjacent stories.
- [ ] Choose the model using `docs/MODEL_SELECTION_POLICY.md`.
- [ ] Create or use one branch for that single story only.
- [ ] Run validation evidence before commit.
- [ ] Record rollback expectations and a stop condition if validation fails three times.

## Execution Rules
- Each future Codex run must implement exactly one TM story.
- Codex must not implement adjacent stories in the same run.
- Validation evidence is required before commit.
- Rollback notes are required before merge.
- If validation fails three times, stop and escalate instead of expanding scope.

## Story To Implementation Flow
1. Start from the story map and identify the one active story.
2. Read only the planning artifacts needed for that story.
3. Check the readiness checklist and relevant validation gates.
4. Implement only the active story's scope.
5. Verify the result with the documented validation commands.
6. Capture risks, rollback expectations, and any skipped validation.
7. Commit only after the boundary checklist is satisfied.

## Out Of Bounds
Do not use this boundary to create backend code, frontend code, database models, Alembic migrations, Docker Compose files, or CI workflows.
