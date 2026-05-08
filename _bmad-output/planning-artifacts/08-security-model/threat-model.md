# Threat Model
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Assets
- User accounts and sessions.
- Organization/workspace/project data.
- Work item content and attachments.
- API tokens and webhook secrets.
- Audit logs.
- Workflow definitions and permissions.

## Threats and Controls

| Threat | Risk | Controls |
|---|---|---|
| Token theft | Account/API compromise | Short access TTL, refresh rotation, token revocation, secure storage |
| Broken RBAC | Tenant data leak | Central permission service, integration tests, audit denied sensitive actions |
| Workflow bypass | Process integrity failure | Server-side transition validation only |
| Webhook abuse | Data exfiltration or spam | HMAC signatures, scoped payloads, delivery limits |
| Secret leakage | Infrastructure compromise | Secret scanning, env/secret manager, redacted logs |
| Attachment malware | User/device risk | File type validation, size limits, future scanning |
| SQL injection | Data compromise | ORM parameterization, query review, validation |
| XSS via comments | Session/data risk | Sanitize rendered content, secure markdown policy |
| CSRF if cookies used | Unauthorized actions | SameSite cookies, CSRF tokens where needed |
| WebSocket leakage | Realtime data leak | Authenticated channels, server-side scope filtering |

## Abuse Cases
- User from Workspace A attempts to access Workspace B project by ID.
- Contributor attempts admin-only workflow change.
- API token with read scope attempts write operation.
- Drag-and-drop UI attempts invalid transition.
- Webhook endpoint is configured to attacker-controlled system by unauthorized user.

## Security Test Requirements
Every abuse case above must become an automated test before production launch.
