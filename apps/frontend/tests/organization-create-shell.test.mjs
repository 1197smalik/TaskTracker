import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const readText = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("organization create shell posts through the authenticated API client and renders backend states", async () => {
  const appSource = await readText("src/App.tsx");
  const pageSource = await readText("src/organizations/OrganizationCreatePage.tsx");
  const apiSource = await readText("src/organizations/api.ts");

  assert.match(appSource, /path="\/organizations\/new"/);
  assert.match(appSource, /<OrganizationCreatePage/);
  assert.match(appSource, /apiClient=\{apiClient\}/);
  assert.match(appSource, /isAuthenticated=\{isAuthenticatedSession\(session\)\}/);
  assert.match(pageSource, /Create the Phase 1 organization boundary with the authenticated API client\./);
  assert.match(pageSource, /Create organization/);
  assert.match(pageSource, /Organization state is ready for workspace setup in the next story\./);
  assert.match(apiSource, /apiClient\.request\("\/api\/v1\/organizations"/);
  assert.match(apiSource, /new OrganizationCreateError/);
  assert.match(apiSource, /field_errors/);
});
