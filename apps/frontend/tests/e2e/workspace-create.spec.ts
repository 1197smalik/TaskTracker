import { expect, test } from "@playwright/test";

test("workspace create route renders the workspace creation shell", async ({
  page,
}) => {
  await page.goto("/organizations/org-1/workspaces/new");

  await expect(page.getByRole("heading", { name: "Create workspace" })).toBeVisible();
  await expect(
    page.getByText(
      "Create the Phase 1 workspace shell inside the selected organization. Project creation stays in the next story."
    )
  ).toBeVisible();
  await expect(page.getByText("Sign in before creating a workspace.")).toBeVisible();
});
