import { expect, test } from "@playwright/test";

test("work item detail requires sign in before backend detail can load", async ({
  page,
}) => {
  await page.goto("/workspace/workspace-1/projects/project-1/work-items/work-item-1");

  await expect(
    page.getByRole("heading", { name: "Project work item detail" })
  ).toBeVisible();
  await expect(
    page.getByText(
      "Detail contract: /api/v1/projects/project-1/work-items/work-item-1"
    )
  ).toBeVisible();
  await expect(
    page.getByText("Sign in to load work item detail.")
  ).toBeVisible();
});
