# API Design Guidelines
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## API Principles
- API-first: frontend and external clients use the same backend contracts.
- Versioned: all routes start with `/api/v1`.
- Resource-oriented where natural, action endpoints where business actions matter.
- Backend returns capabilities and validation errors instead of forcing frontend guesses.

## Endpoint Categories
- Identity: login, refresh, logout, users, memberships, roles.
- Projects: workspaces, projects, boards, sprints, epics, labels.
- Work items: create, update, list, search, transition, link.
- Workflow: definitions, states, transitions, rules, assignment.
- Collaboration: comments, mentions, attachments, notifications, activity.
- Audit: audit logs, security events.
- Integrations: API tokens, webhooks, delivery logs.

## Request/Response Rules
- Use JSON request/response bodies.
- Use consistent snake_case or camelCase. Recommended: snake_case backend contract for Python consistency, frontend client maps as needed.
- Include correlation_id in responses or headers for debugging.
- Use stable error envelope.

## Error Envelope
Every API error should include:
- error_code
- message
- details
- correlation_id
- field_errors where applicable
- retry_after where applicable

## Status Codes
- 200: successful read/update.
- 201: created.
- 202: accepted async processing.
- 204: deleted/no content.
- 400: invalid request.
- 401: unauthenticated.
- 403: authenticated but not authorized.
- 404: not found or inaccessible.
- 409: conflict/version mismatch.
- 422: validation error.
- 429: rate limited.
- 500: unexpected server error.

## Pagination
- Cursor pagination for large lists.
- Response includes items, next_cursor, total only where cheap.
- Avoid expensive total counts on high-volume tables unless cached or approximate.

## Idempotency
Mutation endpoints that may be retried by external clients should accept idempotency keys later. Webhook deliveries must include delivery ids.

## API Security
- All workspace/project endpoints require authentication.
- API tokens must be scoped.
- Sensitive fields are never returned unless explicitly needed and authorized.
- Rate limits vary by endpoint sensitivity.
