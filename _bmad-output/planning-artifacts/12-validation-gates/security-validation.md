# Security Validation
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Required Controls To Test
- Password hashing uses approved algorithm/configuration.
- JWT expiration and invalid token behavior.
- Refresh rotation and reuse detection.
- API token hashing and one-time raw token display.
- RBAC deny-by-default behavior.
- Workspace/project boundary enforcement.
- WebSocket scope filtering.
- Webhook HMAC signing.
- Rate limiting on auth and token endpoints.

## Scanning
- Dependency vulnerabilities.
- Secret scanning.
- Container image scanning before production.
- Static checks for dangerous patterns where practical.

## Abuse Test Matrix
| Abuse Attempt | Expected Result |
|---|---|
| Access another workspace by id | 403 or 404 without data leak |
| Transition without permission | 403 with audit if sensitive |
| Invalid workflow transition | 422/409 with reason |
| Reuse revoked refresh token | 401 and security event |
| Use API token outside scope | 403 |
| Subscribe websocket to unauthorized project | Denied/no events |
