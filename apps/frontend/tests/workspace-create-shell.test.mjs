import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const readText = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("workspace create shell posts through the authenticated API client and routes into workspace context", async () => {
  const appSource = await readText("src/App.tsx");
  const pageSource = await readText("src/workspaces/WorkspaceCreatePage.tsx");
  const apiSource = await readText("src/workspaces/api.ts");

  assert.match(appSource, /path="\/organizations\/:organizationId\/workspaces\/new"/);
  assert.match(appSource, /onWorkspaceCreated=\{handleWorkspaceCreated\}/);
  assert.match(appSource, /fetchWorkspaceNavigation\(apiClient\)/);
  assert.match(appSource, /selectedWorkspaceId: workspace\.id/);
  assert.match(pageSource, /Create the Phase 1 workspace shell inside the selected organization\./);
  assert.match(pageSource, /Create workspace/);
  assert.match(pageSource, /navigate\("\/workspace"\)/);
  assert.match(apiSource, /\/api\/v1\/organizations\/\$\{organizationId\}\/workspaces/);
  assert.match(apiSource, /new WorkspaceCreateError/);
});
