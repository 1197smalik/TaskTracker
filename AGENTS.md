# AGENTS.md

## Purpose
This repository is entering implementation from a BMAD planning baseline. Agents working here must execute implementation as controlled story work, not as open-ended feature development.

## Mandatory Inputs For Every Future Task
Every future Codex task must explicitly reference:
- exactly one story id from `_bmad-output/planning-artifacts/09-story-decomposition/story-map.md` or an equivalent repository-approved story identifier
- the relevant planning artifact(s) that govern the change
- the validation commands that prove the story is complete

If a task does not identify a story id, treat it as incomplete and stop for clarification before implementation.

## Execution Baseline
Use the BMAD planning package under `_bmad-output/planning-artifacts/` as the source of truth.

Minimum artifacts to consult before implementation:
- PRD: `_bmad-output/planning-artifacts/02-prd/prd.md`
- Story map: `_bmad-output/planning-artifacts/09-story-decomposition/story-map.md`
- Execution ordering: `_bmad-output/planning-artifacts/10-dependency-graphs/execution-ordering.md`
- Codex workflow: `_bmad-output/planning-artifacts/11-autonomous-coding-loop/codex-execution-workflow.md`
- Validation gates: `_bmad-output/planning-artifacts/12-validation-gates/validation-gates.md`

Consult additional artifacts only for the domain being changed.

## Required Architecture Summary
Implementation must preserve these decisions from the planning package:
- Architecture starts as a modular monolith.
- Backend owns authentication, authorization, workflow validation, audit logging, and event dispatch rules.
- Frontend is presentation-only for permissions and workflow behavior; it renders backend-provided capabilities and validation responses.
- Work items use one generic typed model instead of separate per-type subsystems.
- Workflow engine is a first-class domain, separate from basic CRUD.
- Audit and outbox/event behavior are part of core write paths.
- Docker Compose is the initial runtime model; design remains Kubernetes-ready.

## Story Execution Rules
- Execute exactly one story at a time for each Codex run.
- Use one branch per story: `story/TM-###-short-title`.
- Do not combine unrelated stories, opportunistic refactors, or speculative scaffolding.
- Do not implement beyond the active story's acceptance criteria.
- Respect dependency order from `_bmad-output/planning-artifacts/10-dependency-graphs/execution-ordering.md`.
- Serialize schema migration work unless explicitly reviewed as safe.

## Definition Of Done
A story is done only when all of the following are true:
- Story acceptance criteria are met.
- Only story-relevant files were changed.
- Required validation commands passed.
- Tests were added or updated where the story changes behavior.
- API, workflow, or architecture docs were updated if contracts changed.
- No secrets, local artifacts, or generated noise were committed.
- PR summary includes story id, scope, validation evidence, risk, and rollback note.

## Blocking Rules
Stop and escalate when:
- requirements conflict with the planning artifacts
- a dependency story is missing or incomplete
- a security-sensitive behavior is unclear
- a migration is not clearly reversible or safely testable
- validation fails after three focused attempts

## Non-Goals During Governance Setup
Until the next story begins, do not add application implementation for FastAPI, React features, database models, Docker runtime files, or tests beyond documentation and repository control artifacts.

## Model Selection
Choose the model based on story complexity:
- Use `GPT-5.4-mini` for narrow documentation-only, file-scaffolding, or simple repository-governance updates.
- Use `GPT-5.4` for normal story execution involving focused reasoning across a small set of files or planning artifacts.
- Use `GPT-5.5` for cross-cutting, ambiguous, migration-sensitive, or higher-risk stories that require deeper reasoning.

Detailed model guidance is defined in `docs/MODEL_SELECTION_POLICY.md`.
