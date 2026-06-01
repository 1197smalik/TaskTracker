import { expect, test } from "@playwright/test";

test("work item list requires sign in before backend data can load", async ({
  page,
}) => {
  await page.goto("/workspace/workspace-1/projects/project-1/work-items");

  await expect(
    page.getByRole("heading", { name: "Project work items" })
  ).toBeVisible();
  await expect(
    page.getByText("List contract: /api/v1/projects/project-1/work-items?limit=50&offset=0")
  ).toBeVisible();
  await expect(
    page.getByText("Sign in to load project work items.")
  ).toBeVisible();
});
