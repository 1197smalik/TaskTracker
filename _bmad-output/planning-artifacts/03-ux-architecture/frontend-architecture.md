# Frontend Architecture
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Stack
React, TypeScript, Vite, shadcn/ui, TanStack Query, Zustand.

## Frontend Responsibility Boundary
The frontend is a presentation and interaction layer. It does not own authorization, workflow rules, or business validation. It renders backend-provided capabilities, reasons, validation errors, and state.

## Application Layers

| Layer | Responsibility |
|---|---|
| App shell | Routing, layout, auth session bootstrapping |
| API client | Typed request/response handling, auth header injection, retry policy |
| Server state | TanStack Query for API data, cache invalidation, optimistic UI only where safe |
| Local UI state | Zustand for drawers, filters, command menu, ephemeral state |
| Component system | shadcn/ui primitives with TaskMaster design conventions |
| Feature modules | identity, project, work-item, workflow, collaboration, integrations |

## Frontend Module Boundaries
- `identity`: login, sessions, workspace/org switcher, role display.
- `projects`: project list, project settings, board/backlog shell.
- `work-items`: list, detail, create/edit forms, metadata panels.
- `workflow`: transition controls, workflow admin screens.
- `collaboration`: comments, mentions, activity feed, notifications.
- `integrations`: API tokens and webhooks admin.

## API Consumption Rules
- Use generated or manually maintained typed clients based on OpenAPI standards.
- Every mutation invalidates or updates relevant TanStack Query caches.
- Frontend must not infer permissions from role names. Backend returns allowed actions/capabilities.
- Frontend must not store refresh tokens in unsafe storage. Token handling must follow security design.

## Realtime Strategy
- WebSocket connection established per authenticated workspace context.
- Events are scoped by workspace/project permissions.
- WebSocket events update query caches, not bypass REST truth.
- Lost connection falls back to polling for critical notification count.

## Error Handling
- 401: session refresh flow or logout.
- 403: show backend-provided permission reason.
- 409: conflict state, refresh entity.
- 422: form validation mapped to fields.
- 429: show retry-after guidance.
- 5xx: user-friendly error plus Sentry capture.

## Performance Requirements
- Board data must be paginated/lazy-loaded.
- Large lists must support virtualization.
- Search/filter changes must debounce.
- Route-level code splitting for admin-heavy features.

## Testing Expectations
- Component tests for shared UI behavior.
- Playwright flows for login, project creation, work item lifecycle, workflow transition, comments, notifications.
- Contract tests against OpenAPI mocks where possible.
