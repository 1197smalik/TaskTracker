import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const readText = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("workspace/project navigation starts from an explicit unavailable state", async () => {
  const navigationSource = await readText("src/projects/navigation.ts");

  assert.match(
    navigationSource,
    /WORKSPACE_PROJECT_NAVIGATION_UNAVAILABLE_REASON\s*=\s*\n\s+"workspace_project_api_not_available"/
  );
  assert.match(navigationSource, /status: "unavailable"/);
  assert.match(navigationSource, /workspaces: \[\]/);
  assert.match(navigationSource, /projects: \[\]/);
  assert.doesNotMatch(navigationSource, /localStorage|sessionStorage|fetch\(/);
});

test("workspace/project shell does not fake authorization or persistence", async () => {
  const componentSource = await readText(
    "src/projects/WorkspaceProjectNavigation.tsx"
  );
  const appSource = await readText("src/App.tsx");

  assert.match(componentSource, /No frontend authorization or membership lookup is inferred/);
  assert.match(componentSource, /backend workspace\/project list APIs exist/);
  assert.match(appSource, /createEmptyWorkspaceProjectNavigation/);
  assert.match(appSource, /\/workspace\/:workspaceId\/projects\/:projectId/);
  assert.doesNotMatch(componentSource, /admin|role|permission|capability/i);
});
