# RBAC Design
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## RBAC Model
TaskMaster uses scoped RBAC. Roles grant permissions within organization, workspace, or project scope.

## Initial Roles

| Role | Scope | Capabilities |
|---|---|---|
| Organization Owner | Organization | Manage org, workspaces, billing later, security settings |
| Workspace Admin | Workspace | Manage workspace users, projects, workflows |
| Project Admin | Project | Manage project settings, workflows, boards |
| Maintainer | Project | Manage work items, sprints, labels, components |
| Contributor | Project | Create/update assigned work, comment, transition allowed states |
| Viewer | Project | Read-only access |
| Integration Bot | Scoped | API-token-specific permissions |

## Permission Examples
- identity.membership.invite
- identity.role.assign
- project.create
- project.update
- workflow.definition.create
- workflow.transition.execute
- work_item.create
- work_item.update
- work_item.delete
- comment.create
- audit.read
- integration.webhook.manage

## Permission Evaluation
Inputs:
- actor_id or API token actor.
- organization/workspace/project scope.
- action permission.
- entity-specific constraints.

Output:
- allowed boolean.
- denial reason for UX.
- audit marker when sensitive.

## Design Rules
- Role names are not hardcoded in feature logic.
- Permissions are checked by backend application services.
- UI must not infer permission from role label.
- Superuser bypass is not allowed in production business flows; use explicit admin permissions.

## Future Enhancements
- Custom roles.
- Attribute-based checks for enterprise plans.
- Temporary elevated access.
- Approval workflows for sensitive changes.
