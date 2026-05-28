import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const readText = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("work item board API contract uses backend-owned workflow state catalog", async () => {
  const apiSource = await readText("src/work-items/api.ts");

  assert.match(apiSource, /type ProjectWorkflowStateResponse =/);
  assert.match(apiSource, /position: number/);
  assert.match(apiSource, /type ProjectWorkflowStateCatalogResponse =/);
  assert.match(apiSource, /workflow_definition_id: string/);
  assert.match(apiSource, /buildProjectWorkflowStatesUrl/);
  assert.match(
    apiSource,
    /\/api\/v1\/projects\/\$\{encodeURIComponent\(projectId\)\}\/workflow-states/
  );
  assert.match(apiSource, /buildProjectBoardPath/);
});

test("work item board page renders backend-provided columns and transition calls", async () => {
  const pageSource = await readText("src/work-items/WorkItemBoardPage.tsx");
  const appSource = await readText("src/App.tsx");
  const projectSource = await readText("src/projects/WorkspaceProjectNavigation.tsx");

  assert.match(pageSource, /Project board/);
  assert.match(pageSource, /Workflow states contract:/);
  assert.match(pageSource, /Work items contract:/);
  assert.match(pageSource, /response\.workflowStates\.states\.map/);
  assert.match(pageSource, /transitionProjectWorkItem/);
  assert.match(pageSource, /expected_version: workItem\.version/);
  assert.match(pageSource, /source_state_id: workItem\.current_state_id/);
  assert.match(pageSource, /target_state_id: targetStateId/);
  assert.match(pageSource, /result\.response\.work_item/);
  assert.match(pageSource, /Failed transition leaves board state unchanged/);
  assert.match(pageSource, /does not infer transition legality or permissions/);
  assert.doesNotMatch(pageSource, /localStorage|sessionStorage|role|admin/i);
  assert.match(
    appSource,
    /\/workspace\/:workspaceId\/projects\/:projectId\/board/
  );
  assert.match(projectSource, /View board/);
});
