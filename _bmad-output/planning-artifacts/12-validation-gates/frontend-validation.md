# Frontend Validation
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Required Commands
- `npm run lint`
- `npm run typecheck`
- `npm run test`
- `npm run build`
- `npx playwright test`

## Critical User Flows
- Login/session restore/logout.
- Switch organization/workspace.
- Open project board.
- Create work item.
- View work item detail.
- Transition work item through allowed transition.
- Attempt forbidden action and show backend reason.
- Add comment and mention user.
- Receive notification.

## Frontend-Specific Blocking Failures
- Authorization logic inferred locally from role names.
- UI allows mutation without handling 403/409/422.
- Board drag-and-drop updates UI without backend transition success.
- Type errors in API contracts.
- Broken production build.
