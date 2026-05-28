import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const readText = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("work item detail API contract matches the backend detail route", async () => {
  const apiSource = await readText("src/work-items/api.ts");

  assert.match(apiSource, /buildProjectWorkItemDetailUrl/);
  assert.match(
    apiSource,
    /\/api\/v1\/projects\/\$\{encodeURIComponent\(projectId\)\}\/work-items\/\$\{encodeURIComponent\(workItemId\)\}/
  );
  assert.match(apiSource, /buildProjectWorkItemDetailPath/);
  assert.match(
    apiSource,
    /\/workspace\/\$\{encodeURIComponent\(workspaceId\)\}\/projects\/\$\{encodeURIComponent\(projectId\)\}\/work-items\/\$\{encodeURIComponent\(workItemId\)\}/
  );
});

test("work item detail page stays presentation-only and future-safe", async () => {
  const pageSource = await readText("src/work-items/WorkItemDetailPage.tsx");
  const appSource = await readText("src/App.tsx");
  const listSource = await readText("src/work-items/WorkItemListPage.tsx");

  assert.match(pageSource, /status: "not_configured"/);
  assert.match(pageSource, /Project work item detail/);
  assert.match(pageSource, /Detail contract:/);
  assert.match(
    pageSource,
    /does not infer comment, activity, attachment, or workflow capabilities/
  );
  assert.match(
    pageSource,
    /Comments,\s+attachments,\s+activity,\s+and transition controls are handled by\s+later frontend stories/
  );
  assert.doesNotMatch(pageSource, /fetch\(|localStorage|sessionStorage|role|admin/i);
  assert.match(
    appSource,
    /\/workspace\/:workspaceId\/projects\/:projectId\/work-items\/:workItemId/
  );
  assert.match(listSource, /buildProjectWorkItemDetailPath/);
});
