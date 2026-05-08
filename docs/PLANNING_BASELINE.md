# Planning Baseline

TaskMaster's implementation baseline is the BMAD planning package at `_bmad-output/planning-artifacts/`.

## Available Planning Package
The planning package currently includes the enterprise planning structure needed to begin controlled implementation:
- product discovery
- PRD
- UX architecture
- system architecture
- domain modeling
- database design
- API contracts
- security model
- story decomposition
- dependency graphs
- autonomous coding loop guidance
- validation gates
- production hardening
- DevOps and infrastructure guidance
- testing strategy
- observability guidance
- risk analysis
- roadmap
- implementation readiness

## How It Will Be Used
- Implementation must be story-driven.
- Future work must follow the story map and dependency ordering.
- Codex tasks must reference the relevant story id and planning artifact paths before any code change.
- Validation must follow the applicable backend, frontend, infrastructure, security, and test gates.
- Planning artifacts are the source of truth until an implementation story explicitly changes them.

## Boundaries
- Do not modify planning artifacts in this step.
- Do not create backend, frontend, infra, or application code here.
- Use this document only to orient future implementation work.
