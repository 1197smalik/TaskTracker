import { expect, test } from "@playwright/test";

test("rbac workspace shell does not advertise local-only navigation copy", async ({
  page,
}) => {
  await page.goto("/workspace");

  await expect(page.getByRole("heading", { name: "Workspace home" })).toBeVisible();
  await expect(
    page.getByText("local manual navigation only", { exact: false })
  ).toHaveCount(0);
  await expect(
    page
      .getByLabel("Workspace and project navigation")
      .getByText(
        "Workspace and project navigation is unavailable right now. Backend-owned visibility rules decide which resources appear here."
      )
      .first()
  ).toBeVisible();
});
