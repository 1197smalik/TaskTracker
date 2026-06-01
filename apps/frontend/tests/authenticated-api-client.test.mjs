import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const readText = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("authenticated api client centralizes bearer attachment and single refresh retry", async () => {
  const clientSource = await readText("src/identity/apiClient.ts");

  assert.match(clientSource, /createAuthenticatedApiClient/);
  assert.match(clientSource, /headers\.set\("Authorization", `Bearer \$\{accessToken\}`\)/);
  assert.match(clientSource, /if \(response\.status !== 401 \|\| hasRetried\)/);
  assert.match(clientSource, /const renewedSession = await refreshSession\(\)/);
  assert.match(clientSource, /return await requestWithAuthentication\(path, init, true\)/);
  assert.doesNotMatch(clientSource, /refresh_token/i);
});

test("app and protected callsites route through the authenticated api client", async () => {
  const appSource = await readText("src/App.tsx");
  const navigationSource = await readText("src/projects/navigation.ts");
  const workItemApiSource = await readText("src/work-items/api.ts");

  assert.match(appSource, /createAuthenticatedApiClient/);
  assert.match(appSource, /fetchWorkspaceNavigation\(apiClient\)/);
  assert.match(appSource, /fetchProjectNavigation\(apiClient, projectNavigation\.selectedWorkspaceId\)/);
  assert.match(appSource, /<WorkItemListPage apiClient=\{apiClient\} sessionStatus=\{session\.status\} \/>/);
  assert.match(appSource, /<WorkItemBoardPage apiClient=\{apiClient\} \/>/);
  assert.match(appSource, /<WorkItemDetailPage apiClient=\{apiClient\} \/>/);
  assert.match(navigationSource, /apiClient\.getJson/);
  assert.match(workItemApiSource, /apiClient\.request/);
});
