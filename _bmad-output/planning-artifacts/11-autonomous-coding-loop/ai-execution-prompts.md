# AI Execution Prompts
> Project: TaskMaster  
> Classification: Internal planning artifact  
> Scope: Enterprise SaaS planning, architecture, workflow, validation, and production readiness  
> Implementation code: intentionally excluded

## Master Story Execution Prompt
Use this prompt for each implementation story:

```text
You are implementing exactly one TaskMaster story.
Story ID: <TM-###>
Story Title: <title>

Read the relevant planning artifacts under _bmad-output/planning-artifacts before changing files.
Implement only this story. Do not add unrelated features. Do not skip validation.

Required behavior:
1. Identify dependencies and confirm they exist.
2. Make the smallest production-quality change that satisfies the story.
3. Preserve domain boundaries.
4. Add or update tests.
5. Run the story validation commands.
6. Provide a PR summary with risks and rollback notes.

Hard rules:
- Backend owns permissions, workflow validation, audit logging, and business rules.
- Frontend must not implement authorization logic.
- No secrets in repository.
- No implementation shortcuts that violate architecture docs.
- If blocked after three attempts, stop and produce an escalation report.
```

## Failure Recovery Prompt
```text
The story validation failed.
Analyze the failure, identify root cause, and apply the smallest correction.
Do not broaden scope.
Run the same validation again.
If this is the third failure, stop and produce an escalation report with exact failing command, logs summary, probable cause, and recommended next action.
```

## PR Review Prompt
```text
Review this PR against TaskMaster architecture and story requirements.
Check:
- Scope control
- Domain boundaries
- Security/RBAC correctness
- Workflow/audit/event correctness
- Test adequacy
- Migration safety
- API contract consistency
- Rollback clarity
Return blocking issues first.
```
