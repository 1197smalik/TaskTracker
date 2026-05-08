# Story Dependency Graph and Execution Ordering
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Execution Waves

### Wave 0: Foundation
TM-001 to TM-006.

### Wave 1: Identity Foundation
TM-007 to TM-025.

### Wave 2: Project and Work Item Foundation
TM-026 to TM-041.

### Wave 3: Workflow Engine
TM-042 to TM-049.

### Wave 4: Audit, Events, Collaboration
TM-050 to TM-073.

### Wave 5: Integrations and Realtime
TM-074 to TM-083.

### Wave 6: Frontend Product Flows
TM-084 to TM-090.

### Wave 7: Observability, Security, CI, Smoke Tests
TM-091 to TM-100.

## Story Graph Snapshot
```mermaid
flowchart TD
  TM001[TM-001] --> TM002[TM-002]
  TM001 --> TM003[TM-003]
  TM001 --> TM004[TM-004]
  TM002 --> TM005[TM-005]
  TM005 --> TM006[TM-006]
  TM005 --> TM007[TM-007 User Model]
  TM007 --> TM008[Users Migration]
  TM007 --> TM017[Password Hashing]
  TM017 --> TM018[JWT Utility]
  TM018 --> TM019[Refresh Token Model]
  TM019 --> TM020[Login]
  TM019 --> TM021[Refresh]
  TM019 --> TM022[Logout]
  TM007 --> TM009[Organization]
  TM009 --> TM011[Workspace]
  TM011 --> TM013[Membership]
  TM013 --> TM015[Roles Permissions]
  TM015 --> TM023[RBAC Evaluator]
  TM018 --> TM024[Auth Dependency]
  TM023 --> TM025[RBAC Dependency]
  TM011 --> TM026[Project]
  TM026 --> TM035[WorkItem]
  TM035 --> TM037[Create WorkItem]
  TM037 --> TM038[Detail]
  TM037 --> TM039[List]
  TM037 --> TM040[Update]
  TM026 --> TM042[Workflow Definition]
  TM042 --> TM043[States]
  TM043 --> TM044[Transitions]
  TM044 --> TM045[Rules]
  TM045 --> TM048[Validator]
  TM048 --> TM049[Transition Endpoint]
  TM049 --> TM054[Transition Audit]
  TM037 --> TM053[Create Audit]
  TM050[Audit Model] --> TM052[Audit Writer]
  TM052 --> TM053
  TM052 --> TM054
  TM056[Outbox] --> TM057[Outbox Service]
  TM057 --> TM058[Created Event]
  TM057 --> TM059[Transitioned Event]
  TM057 --> TM061[Dispatcher]
  TM063[Comments] --> TM064[Mentions]
  TM064 --> TM065[Notifications]
  TM065 --> TM082[WS Notifications]
  TM077[Webhooks] --> TM080[Delivery Worker]
```

## Parallel Workstreams
- Workstream A: Identity and RBAC.
- Workstream B: Project metadata.
- Workstream C: Work item and workflow.
- Workstream D: Audit/events/collaboration.
- Workstream E: Frontend once contracts stabilize.
- Workstream F: Observability/security gates from early foundation onward.

## Merge Rule
Only merge stories that pass local validation and CI. Stories that alter contracts must update contract docs/tests in the same PR.
