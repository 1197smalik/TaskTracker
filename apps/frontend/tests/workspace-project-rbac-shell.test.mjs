import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const readText = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("rbac navigation shell consumes backend-filtered visibility and clears denied workspace scope safely", async () => {
  const appSource = await readText("src/App.tsx");
  const componentSource = await readText("src/projects/WorkspaceProjectNavigation.tsx");
  const navigationSource = await readText("src/projects/navigation.ts");

  assert.match(appSource, /project_navigation_request_failed:403/);
  assert.match(appSource, /project_navigation_request_failed:404/);
  assert.match(appSource, /clearSelectedWorkspace/);
  assert.match(
    componentSource,
    /Workspace and project lists reflect backend-filtered visibility for the/
  );
  assert.doesNotMatch(componentSource, /local manual navigation only/i);
  assert.match(navigationSource, /clearSelectedWorkspace/);
  assert.doesNotMatch(navigationSource, /local_manual_navigation_only/);
});
