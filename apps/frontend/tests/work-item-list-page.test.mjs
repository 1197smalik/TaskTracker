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
  assert.match(apiSource, /\/api\/v1\/projects\/\$\{encodeURIComponent\(projectId\)\}\/work-items/);
  assert.match(apiSource, /limit: String\(params\.limit\)/);
  assert.match(apiSource, /offset: String\(params\.offset\)/);
});

test("work item list page does not fake data or authorization", async () => {
  const pageSource = await readText("src/work-items/WorkItemListPage.tsx");
  const appSource = await readText("src/App.tsx");

  assert.match(pageSource, /status: "not_configured"/);
  assert.match(pageSource, /authenticated API client/);
  assert.match(pageSource, /does not infer project access or fake work item persistence/);
  assert.doesNotMatch(pageSource, /fetch\(|localStorage|sessionStorage|role|admin/i);
  assert.match(appSource, /\/workspace\/:workspaceId\/projects\/:projectId\/work-items/);
});
