import { expect, test } from "@playwright/test";

test("public frontend shell routes remain reachable", async ({ page }) => {
  await page.goto("/login");
  await expect(
    page.getByRole("heading", { name: "Sign in to TaskMaster" })
  ).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();

  await page.goto("/workspace");
  await expect(
    page.getByText(
      "Recent projects, assigned work, sprint health, and activity will render here after backend workspace/project list APIs exist."
    )
  ).toBeVisible();
});
