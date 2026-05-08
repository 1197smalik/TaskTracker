# UX Architecture
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## UX North Star
TaskMaster must feel fast like Linear, structured like Jira, and developer-native like GitHub Issues. The interface should expose power without forcing every user through admin-heavy screens.

## Information Architecture

- Global shell: organization switcher, workspace switcher, command menu, notifications, user menu.
- Workspace home: recent projects, assigned work, sprint health, activity.
- Project area: board, backlog, active sprint, epics, milestones, settings.
- Work item detail: title, status, type, priority, assignee, description, comments, activity, audit-visible changes.
- Workflow admin: definitions, states, transitions, rules, preview simulator.
- Integration admin: API tokens, webhooks, integration events.

## Core Navigation Model
Navigation must support both managers and developers:

1. Workspace-first for organization context.
2. Project-first for team delivery.
3. Command-first for power users.
4. URL-addressable pages for shareability.
5. Filterable and saved views for repeated workflows.

## UX Principles
- Optimize frequent actions: create work item, assign, transition, comment, search.
- Keep enterprise controls discoverable but not intrusive.
- Make permissions visible through disabled actions with backend-provided reasons.
- Separate activity feed from audit log: activity is collaborative; audit is compliance/security.
- Make workflow transitions explicit; never hide backend validation failure.

## Key Screens

### Dashboard
Shows assigned items, mentioned items, due soon, recent activity, and sprint health. It should not become an overloaded analytics dashboard in the first release.

### Project Board
Columns map to workflow states. Board interactions call backend transition APIs. Drag-and-drop is allowed only if backend validates transition.

### Backlog
Backlog supports triage, ranking, sprint assignment, batch label/component assignment, and quick filters.

### Work Item Detail
The detail page must support collaborative work without forcing navigation away. Key sections: metadata, description, workflow status, comments, attachments, related items, activity.

### Workflow Builder
Initial version can be form-based rather than visual. Required capabilities: create workflow definition, define states, define transitions, assign roles, configure required fields.

## Accessibility Requirements
- Keyboard-accessible command menu and core forms.
- WCAG-conscious contrast and focus indicators.
- No interaction available only through drag-and-drop.
- Form errors must be readable and actionable.

## UX Tradeoffs
- A visual workflow builder is attractive but expensive. Start with structured forms plus preview/simulation.
- Board drag-and-drop is useful but must not bypass backend rules.
- Advanced analytics can wait; operational clarity matters first.
