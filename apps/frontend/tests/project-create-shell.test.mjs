import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const readText = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("project create shell posts through the authenticated API client and routes into project context", async () => {
  const appSource = await readText("src/App.tsx");
  const pageSource = await readText("src/projects/ProjectCreatePage.tsx");
  const apiSource = await readText("src/projects/api.ts");

  assert.match(appSource, /path="\/workspaces\/:workspaceId\/projects\/new"/);
  assert.match(appSource, /onProjectCreated=\{handleProjectCreated\}/);
  assert.match(appSource, /fetchProjectNavigation\(apiClient, project\.workspaceId\)/);
  assert.match(appSource, /selectedProjectId: project\.id/);
  assert.match(
    pageSource,
    /Create the Phase 1 project shell inside the selected workspace\. Boards and/
  );
  assert.match(pageSource, /Create project/);
  assert.match(pageSource, /navigate\(`\/workspace\/\$\{workspaceId\}\/projects\/\$\{project\.id\}`\)/);
  assert.match(apiSource, /\/api\/v1\/projects\/workspaces\/\$\{workspaceId\}\/projects/);
  assert.match(apiSource, /new ProjectCreateError/);
});
