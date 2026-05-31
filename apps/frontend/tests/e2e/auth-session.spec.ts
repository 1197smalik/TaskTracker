import { expect, test } from "@playwright/test";

test("auth keeps a signed-in session alive through timed refresh and logout", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const originalFetch = window.fetch.bind(window);
    let refreshCount = 0;

    const jsonResponse = (body: unknown, status = 200) =>
      new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      });

    window.fetch = async (input, init) => {
      const url = typeof input === "string" ? input : input.url;

      if (url.endsWith("/api/v1/auth/login")) {
        return jsonResponse({
          access_token: "access-token-1",
          refresh_token: "refresh-token-1",
          token_type: "bearer",
          expires_in: 61,
        });
      }

      if (url.endsWith("/api/v1/auth/refresh")) {
        refreshCount += 1;
        return jsonResponse({
          access_token: `access-token-${refreshCount + 1}`,
          refresh_token: `refresh-token-${refreshCount + 1}`,
          token_type: "bearer",
          expires_in: 61,
        });
      }

      if (url.endsWith("/api/v1/auth/logout")) {
        return jsonResponse({ revoked: true });
      }

      return originalFetch(input, init);
    };
  });

  await page.goto("/login");
  await page.getByLabel("Email").fill("person@example.com");
  await page.getByLabel("Password").fill("secret");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/\/workspace$/);
  await expect(page.getByText("Signed in")).toBeVisible();
  await expect
    .poll(() => page.evaluate(() => window.localStorage.getItem("taskmaster.refresh_token")))
    .toBe("refresh-token-1");

  await expect
    .poll(() => page.evaluate(() => window.localStorage.getItem("taskmaster.refresh_token")))
    .toBe("refresh-token-2");
  await expect(page.getByText("Signed in")).toBeVisible();

  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByText("Signed out")).toBeVisible();
  await expect
    .poll(() => page.evaluate(() => window.localStorage.getItem("taskmaster.refresh_token")))
    .toBe(null);
});

test("auth distinguishes invalid credentials", async ({ page }) => {
  await page.addInitScript(() => {
    const originalFetch = window.fetch.bind(window);

    const jsonResponse = (body: unknown, status = 200) =>
      new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      });

    window.fetch = async (input, init) => {
      const url = typeof input === "string" ? input : input.url;

      if (url.endsWith("/api/v1/auth/login")) {
        return jsonResponse(
          {
            error_code: "invalid_credentials",
            message: "Email or password is incorrect.",
          },
          401
        );
      }

      return originalFetch(input, init);
    };
  });

  await page.goto("/login");
  await page.getByLabel("Email").fill("person@example.com");
  await page.getByLabel("Password").fill("wrong-secret");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page.getByText("Email or password is incorrect.")).toBeVisible();
});

test("auth distinguishes expired sessions during refresh recovery", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const originalFetch = window.fetch.bind(window);
    let loginCompleted = false;

    const jsonResponse = (body: unknown, status = 200) =>
      new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      });

    window.fetch = async (input, init) => {
      const url = typeof input === "string" ? input : input.url;

      if (url.endsWith("/api/v1/auth/login")) {
        loginCompleted = true;
        return jsonResponse({
          access_token: "access-token-1",
          refresh_token: "refresh-token-1",
          token_type: "bearer",
          expires_in: 61,
        });
      }

      if (url.endsWith("/api/v1/auth/refresh") && loginCompleted) {
        return jsonResponse(
          {
            error_code: "expired_session",
            message: "Session expired. Sign in again.",
          },
          401
        );
      }

      return originalFetch(input, init);
    };
  });

  await page.goto("/login");
  await page.getByLabel("Email").fill("person@example.com");
  await page.getByLabel("Password").fill("secret");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page.getByText("Signed in")).toBeVisible();
  await expect(page.getByText("Your session expired. Sign in again.")).toBeVisible();
  await expect(page.getByText("Signed out")).toBeVisible();
});

test("auth distinguishes revoked sessions during refresh recovery", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const originalFetch = window.fetch.bind(window);
    let loginCompleted = false;

    const jsonResponse = (body: unknown, status = 200) =>
      new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      });

    window.fetch = async (input, init) => {
      const url = typeof input === "string" ? input : input.url;

      if (url.endsWith("/api/v1/auth/login")) {
        loginCompleted = true;
        return jsonResponse({
          access_token: "access-token-1",
          refresh_token: "refresh-token-1",
          token_type: "bearer",
          expires_in: 61,
        });
      }

      if (url.endsWith("/api/v1/auth/refresh") && loginCompleted) {
        return jsonResponse(
          {
            error_code: "revoked_session",
            message: "Session was revoked. Sign in again.",
          },
          401
        );
      }

      return originalFetch(input, init);
    };
  });

  await page.goto("/login");
  await page.getByLabel("Email").fill("person@example.com");
  await page.getByLabel("Password").fill("secret");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page.getByText("Signed in")).toBeVisible();
  await expect(page.getByText("Your session was revoked. Sign in again.")).toBeVisible();
  await expect(page.getByText("Signed out")).toBeVisible();
});
