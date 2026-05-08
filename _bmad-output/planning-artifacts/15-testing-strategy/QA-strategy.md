# QA Strategy
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## QA Objectives
QA validates not just visible behavior, but enterprise readiness: security boundaries, workflow correctness, auditability, reliability, and operational behavior.

## QA Phases
1. Story-level validation.
2. Epic-level integration testing.
3. Regression testing.
4. Security and abuse testing.
5. Performance baseline testing.
6. Release candidate smoke testing.

## Manual QA Focus
Manual QA should focus on user workflows and edge cases that automation may miss:
- Workflow configuration usability.
- Permission-denied UX.
- Board drag-and-drop behavior.
- Comment/mention collaboration.
- Recovery after websocket disconnect.

## Release QA Checklist
- Login/logout/refresh stable.
- Workspace/project isolation verified.
- Work item lifecycle works.
- Workflow invalid transitions blocked.
- Audit logs created.
- Notifications delivered.
- Critical dashboards healthy.
- Error tracking quiet after smoke tests.
