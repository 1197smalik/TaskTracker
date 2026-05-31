import { expect, test } from "@playwright/test";

test("project create route renders the project creation shell", async ({
  page,
}) => {
  await page.goto("/workspaces/workspace-1/projects/new");

  await expect(page.getByRole("heading", { name: "Create project" })).toBeVisible();
  await expect(
    page.getByText(
      "Create the Phase 1 project shell inside the selected workspace. Boards and work item wiring stay in later stories."
    )
  ).toBeVisible();
  await expect(page.getByText("Sign in before creating a project.")).toBeVisible();
});
