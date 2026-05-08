# Model Selection Policy

## Purpose
This document defines which model to use for a TaskMaster story based on scope, risk, and reasoning depth.

## Core Rule
- Choose one model for the active story before implementation begins.
- The selected model must match story complexity.
- Default to the lowest-capability model that can complete the story safely.
- Escalate to a stronger model when ambiguity, cross-cutting impact, or validation risk increases.

## `GPT-5.4-mini`
Use `GPT-5.4-mini` for:
- documentation-only stories
- repository scaffolding and placeholder files
- narrow governance updates
- simple validation or inventory checks
- simple tests and lint fixes

Do not use `GPT-5.4-mini` for:
- migration design
- security-sensitive implementation
- cross-domain refactors
- ambiguous stories that require reconciling multiple planning artifacts

## `GPT-5.4`
Use `GPT-5.4` for:
- normal backend implementation
- normal frontend implementation
- focused backend, frontend, infrastructure, or test changes
- stories that require reading a limited set of planning artifacts
- stories with moderate validation and rollback reasoning

`GPT-5.4` is the default model for normal TaskMaster execution.

## `GPT-5.5`
Use `GPT-5.5` for:
- auth work
- RBAC work
- workflow engine work
- security work
- complex debugging
- production hardening
- stories that span multiple architectural concerns within one approved scope
- migration-sensitive or rollback-sensitive work
- stories with unclear edge cases or conflicting constraints
- tasks that need deeper synthesis across planning, validation, and readiness documents

## Escalation Triggers
Switch to a stronger model when:
- requirements are ambiguous
- the story touches auth, RBAC, workflow validation, audit, or outbox behavior
- failure impact is hard to reverse
- validation has failed repeatedly and deeper diagnosis is needed

## Repository Alignment
This policy supports the BMAD execution baseline in:
- `_bmad-output/planning-artifacts/11-autonomous-coding-loop/codex-execution-workflow.md`
- `_bmad-output/planning-artifacts/12-validation-gates/validation-gates.md`
- `_bmad-output/planning-artifacts/19-implementation-readiness/implementation-readiness-report.md`
