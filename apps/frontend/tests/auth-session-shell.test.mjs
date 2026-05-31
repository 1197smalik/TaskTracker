import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const readText = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("auth session contract keeps token storage explicit and frontend-owned auth decisions out", async () => {
  const sessionSource = await readText("src/identity/session.ts");

  assert.match(sessionSource, /AUTH_LOGIN_ENDPOINT = "\/api\/v1\/auth\/login"/);
  assert.match(sessionSource, /AUTH_REFRESH_ENDPOINT = "\/api\/v1\/auth\/refresh"/);
  assert.match(sessionSource, /AUTH_LOGOUT_ENDPOINT = "\/api\/v1\/auth\/logout"/);
  assert.match(sessionSource, /accessToken: "memory_only"/);
  assert.match(sessionSource, /refreshToken: "local_storage_rotating"/);
  assert.match(sessionSource, /authorization: "backend_owned"/);
  assert.match(sessionSource, /localStorage/);
  assert.doesNotMatch(sessionSource, /document\.cookie/);
});

test("app shell wires a real auth session boundary and login UI", async () => {
  const appSource = await readText("src/App.tsx");
  const shellSource = await readText("src/routes/AppShell.tsx");
  const loginPageSource = await readText("src/identity/LoginPage.tsx");

  assert.match(appSource, /createCheckingSession/);
  assert.match(appSource, /refreshSession/);
  assert.match(appSource, /handleLogin/);
  assert.match(appSource, /session=\{session\}/);
  assert.match(loginPageSource, /Use the backend auth endpoints to start or restore a Phase 1 session\./);
  assert.match(loginPageSource, /Email/);
  assert.match(loginPageSource, /Password/);
  assert.match(shellSource, /Authentication session/);
  assert.match(shellSource, /isAuthenticatedSession/);
  assert.match(shellSource, /Sign out/);
});
