import { expect, test } from "@playwright/test";

test("login shell and work-item lifecycle routes stay deterministic", async ({
  page,
}) => {
  await page.goto("/login");

  await expect(
    page.getByRole("heading", { name: "Sign in to TaskMaster" })
  ).toBeVisible();
  await expect(
    page.getByText("Use the backend auth endpoints to start or restore a Phase 1 session.")
  ).toBeVisible();

  await page.goto("/workspace");

  await expect(
    page.getByRole("heading", { name: "Workspace home" })
  ).toBeVisible();
  await expect(
    page.getByText("Recent projects, assigned work, sprint health, and activity will render here after backend workspace/project list APIs exist.")
  ).toBeVisible();

  await page.goto("/workspace/workspace-1/projects/project-1");

  await expect(
    page.getByRole("heading", { name: "Project shell" })
  ).toBeVisible();
  await page.getByRole("link", { name: "View work items" }).click();

  await expect(page).toHaveURL(
    /\/workspace\/workspace-1\/projects\/project-1\/work-items$/
  );
  await expect(
    page.getByRole("heading", { name: "Project work items" })
  ).toBeVisible();
  await expect(
    page.getByText("List contract: /api/v1/projects/project-1/work-items?limit=50&offset=0")
  ).toBeVisible();
  await expect(
    page.getByText("Work item data is waiting for an authenticated API client. This page does not infer project access or fake work item persistence.")
  ).toBeVisible();

  await page.goto(
    "/workspace/workspace-1/projects/project-1/work-items/work-item-1"
  );

  await expect(
    page.getByRole("heading", { name: "Project work item detail" })
  ).toBeVisible();
  await expect(
    page.getByText("Detail contract: /api/v1/projects/project-1/work-items/work-item-1")
  ).toBeVisible();
  await expect(
    page
      .getByRole("region", { name: "Workflow transition control" })
      .getByText(
        "Transition contract: /api/v1/projects/project-1/work-items/work-item-1/transition"
      )
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Transition via backend" })
  ).toBeDisabled();
  await page.getByRole("link", { name: "Back to work items" }).click();

  await expect(page).toHaveURL(
    /\/workspace\/workspace-1\/projects\/project-1\/work-items$/
  );

  await page.goto("/workspace/workspace-1/projects/project-1/board");

  await expect(
    page.getByRole("heading", { name: "Project board" })
  ).toBeVisible();
  await expect(
    page.getByText("Workflow states contract: /api/v1/projects/project-1/workflow-states")
  ).toBeVisible();
  await expect(
    page.getByText("Work items contract: /api/v1/projects/project-1/work-items?limit=100&offset=0")
  ).toBeVisible();
  await expect(
    page.getByText("Board data is waiting for authenticated API responses. This board does not infer transition legality or permissions. Backend workflow state catalog and transition responses own those outcomes.")
  ).toBeVisible();
});
