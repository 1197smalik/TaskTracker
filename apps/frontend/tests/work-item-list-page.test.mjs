import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const readText = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("work item list API contract matches the backend list route", async () => {
  const apiSource = await readText("src/work-items/api.ts");

  assert.match(apiSource, /type WorkItemResponse =/);
  assert.match(apiSource, /project_id: string/);
  assert.match(apiSource, /typed_metadata: Record<string, unknown>/);
  assert.match(apiSource, /buildProjectWorkItemListUrl/);
  assert.match(apiSource, /async function fetchProjectWorkItems/);
  assert.match(apiSource, /apiClient\.request\(buildProjectWorkItemListUrl\(projectId, params\)\)/);
  assert.match(apiSource, /\/api\/v1\/projects\/\$\{encodeURIComponent\(projectId\)\}\/work-items/);
  assert.match(apiSource, /limit: String\(params\.limit\)/);
  assert.match(apiSource, /offset: String\(params\.offset\)/);
});

test("work item list page loads backend data states without frontend permission logic", async () => {
  const pageSource = await readText("src/work-items/WorkItemListPage.tsx");
  const appSource = await readText("src/App.tsx");

  assert.match(pageSource, /status: "loading"/);
  assert.match(pageSource, /status: "failed"/);
  assert.match(pageSource, /sessionStatus === "checking"/);
  assert.match(pageSource, /sessionStatus !== "authenticated"/);
  assert.match(pageSource, /fetchProjectWorkItems\(apiClient, projectId/);
  assert.match(pageSource, /Loading work items from the backend\./);
  assert.match(pageSource, /Sign in to load project work items\./);
  assert.match(pageSource, /No work items returned for this project\./);
  assert.match(pageSource, /TaskMaster could not load work items from the backend\./);
  assert.doesNotMatch(pageSource, /localStorage|sessionStorage|role|admin/i);
  assert.match(appSource, /\/workspace\/:workspaceId\/projects\/:projectId\/work-items/);
  assert.match(appSource, /<WorkItemListPage apiClient=\{apiClient\} sessionStatus=\{session\.status\} \/>/);
});
