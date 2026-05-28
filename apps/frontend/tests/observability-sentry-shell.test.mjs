import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const readText = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("frontend sentry strategy stays disabled by default and strips sensitive fields", async () => {
  const sentrySource = await readText("src/observability/sentry.tsx");

  assert.match(sentrySource, /FRONTEND_SENTRY_DSN_ENV_VAR = "VITE_SENTRY_DSN"/);
  assert.match(sentrySource, /sendDefaultPii: false/);
  assert.match(sentrySource, /captureUnhandledErrors: true/);
  assert.match(sentrySource, /captureUnhandledRejections: true/);
  assert.match(sentrySource, /captureServerErrors: true/);
  assert.match(sentrySource, /query_string/);
  assert.match(sentrySource, /authorization/);
  assert.match(sentrySource, /password/);
});

test("frontend shell initializes sentry and wraps the app in an error boundary", async () => {
  const mainSource = await readText("src/main.tsx");
  const sentrySource = await readText("src/observability/sentry.tsx");

  assert.match(mainSource, /initFrontendSentry\(\)/);
  assert.match(mainSource, /<AppErrorBoundary>/);
  assert.match(sentrySource, /Something went wrong\. Please try again\./);
  assert.match(sentrySource, /Sentry\.captureException/);
  assert.match(sentrySource, /frontend\.server_error/);
});
