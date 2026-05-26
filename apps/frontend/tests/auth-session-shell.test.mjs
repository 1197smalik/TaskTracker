import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const readText = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("auth session contract keeps token storage explicit and frontend-owned auth decisions out", async () => {
  const sessionSource = await readText("src/identity/session.ts");

  assert.match(sessionSource, /AUTH_LOGIN_ENDPOINT = "\/api\/v1\/auth\/login"/);
  assert.match(sessionSource, /AUTH_REFRESH_ENDPOINT = "\/api\/v1\/auth\/refresh"/);
  assert.match(sessionSource, /accessToken: "memory_only"/);
  assert.match(sessionSource, /refreshToken: "not_stored_by_frontend_shell"/);
  assert.match(sessionSource, /authorization: "backend_owned"/);
  assert.doesNotMatch(sessionSource, /localStorage|sessionStorage|document\.cookie/);
});

test("app shell wires a session boundary without implementing login", async () => {
  const appSource = await readText("src/App.tsx");
  const shellSource = await readText("src/routes/AppShell.tsx");

  assert.match(appSource, /createAnonymousSession/);
  assert.match(appSource, /<AppShell session=\{session\}/);
  assert.match(appSource, /credential\s+verification is not implemented yet/i);
  assert.match(shellSource, /Authentication session/);
  assert.match(shellSource, /isAuthenticatedSession/);
});
