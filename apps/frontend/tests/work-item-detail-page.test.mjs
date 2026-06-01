import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const readText = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("work item detail API contract matches the backend detail route", async () => {
  const apiSource = await readText("src/work-items/api.ts");

  assert.match(apiSource, /buildProjectWorkItemDetailUrl/);
  assert.match(apiSource, /async function fetchProjectWorkItemDetail/);
  assert.match(
    apiSource,
    /\/api\/v1\/projects\/\$\{encodeURIComponent\(projectId\)\}\/work-items\/\$\{encodeURIComponent\(workItemId\)\}/
  );
  assert.match(apiSource, /buildProjectWorkItemDetailPath/);
  assert.match(
    apiSource,
    /\/workspace\/\$\{encodeURIComponent\(workspaceId\)\}\/projects\/\$\{encodeURIComponent\(projectId\)\}\/work-items\/\$\{encodeURIComponent\(workItemId\)\}/
  );
  assert.match(apiSource, /type WorkflowTransitionRequest =/);
  assert.match(apiSource, /expected_version: number/);
  assert.match(apiSource, /target_state_id: string/);
  assert.match(apiSource, /source_state_id\?: string \| null/);
  assert.match(apiSource, /type WorkflowTransitionResponse =/);
  assert.match(apiSource, /transition_id: string/);
  assert.match(apiSource, /buildProjectWorkItemTransitionUrl/);
  assert.match(apiSource, /async function transitionProjectWorkItem/);
  assert.match(apiSource, /method: "POST"/);
  assert.match(apiSource, /"Content-Type": "application\/json"/);
  assert.match(apiSource, /JSON\.stringify\(request\)/);
  assert.match(apiSource, /status: "succeeded"/);
  assert.match(apiSource, /status: "failed"/);
  assert.match(
    apiSource,
    /\/api\/v1\/projects\/\$\{encodeURIComponent\(projectId\)\}\/work-items\/\$\{encodeURIComponent\(workItemId\)\}\/transition/
  );
});

test("work item detail page loads backend detail states and keeps transition behavior scoped", async () => {
  const pageSource = await readText("src/work-items/WorkItemDetailPage.tsx");
  const appSource = await readText("src/App.tsx");
  const listSource = await readText("src/work-items/WorkItemListPage.tsx");

  assert.match(pageSource, /status: "loading"/);
  assert.match(pageSource, /status: "failed"/);
  assert.match(pageSource, /fetchProjectWorkItemDetail\(apiClient, projectId, workItemId\)/);
  assert.match(pageSource, /Loading work item detail from the backend\./);
  assert.match(pageSource, /Sign in to load work item detail\./);
  assert.match(pageSource, /This work item was not found\./);
  assert.match(pageSource, /Project work item detail/);
  assert.match(pageSource, /Detail contract:/);
  assert.match(
    pageSource,
    /Transition contract:/
  );
  assert.match(
    pageSource,
    /does not infer allowed transitions or fake workflow\s+execution/
  );
  assert.match(pageSource, /status: "idle"/);
  assert.match(pageSource, /status: "submitting"/);
  assert.match(pageSource, /status: "succeeded"/);
  assert.match(pageSource, /status: "failed"/);
  assert.match(pageSource, /Submitting backend workflow transition request/);
  assert.match(
    pageSource,
    /Backend confirmed the workflow transition and returned the updated work item version/
  );
  assert.match(pageSource, /describeTransitionFailure/);
  assert.match(pageSource, /statusCode === 409/);
  assert.match(pageSource, /statusCode === 400/);
  assert.match(pageSource, /statusCode === 404/);
  assert.match(
    pageSource,
    /expected_version/
  );
  assert.match(
    pageSource,
    /target_state_id/
  );
  assert.match(
    pageSource,
    /source_state_id/
  );
  assert.match(
    pageSource,
    /409 conflict/
  );
  assert.match(
    pageSource,
    /400 validation/
  );
  assert.match(
    pageSource,
    /Comments,\s+attachments,\s+and activity are handled by later frontend\s+stories/
  );
  assert.doesNotMatch(pageSource, /localStorage|sessionStorage|role|admin/i);
  assert.match(
    appSource,
    /\/workspace\/:workspaceId\/projects\/:projectId\/work-items\/:workItemId/
  );
  assert.match(
    appSource,
    /<WorkItemDetailPage\s+apiClient=\{apiClient\}\s+sessionStatus=\{session\.status\}\s+\/>/
  );
  assert.match(listSource, /buildProjectWorkItemDetailPath/);
});
