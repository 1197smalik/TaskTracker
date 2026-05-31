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
  assert.doesNotMatch(navigationSource, /localStorage|sessionStorage/);
});

test("workspace/project shell keeps selection local and explicit", async () => {
  const componentSource = await readText(
    "src/projects/WorkspaceProjectNavigation.tsx"
  );
  const appSource = await readText("src/App.tsx");
  const navigationSource = await readText("src/projects/navigation.ts");

  assert.match(componentSource, /aria-label="Workspace selector"/);
  assert.match(componentSource, /aria-label="Project selector"/);
  assert.match(
    componentSource,
    /Workspace and project lists reflect backend-filtered visibility for the/
  );
  assert.match(componentSource, /No workspaces are available for your current access\./);
  assert.match(componentSource, /No projects are available for the selected workspace/);
  assert.match(appSource, /fetchWorkspaceNavigation/);
  assert.match(appSource, /fetchProjectNavigation/);
  assert.match(appSource, /project_navigation_request_failed:403/);
  assert.match(appSource, /clearSelectedWorkspace/);
  assert.match(appSource, /updateSelectedWorkspace/);
  assert.match(appSource, /updateSelectedProject/);
  assert.match(appSource, /createEmptyWorkspaceProjectNavigation/);
  assert.match(appSource, /\/workspace\/:workspaceId\/projects\/:projectId/);
  assert.match(navigationSource, /\/api\/v1\/projects\/workspaces/);
  assert.doesNotMatch(navigationSource, /local_manual_navigation_only/);
  assert.doesNotMatch(componentSource, /admin|role|permission|capability/i);
});
