import { expect, test } from "@playwright/test";

test("Capture Code Playground Desktop Screenshot", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });

  await page.goto("/login");
  await page.waitForLoadState("domcontentloaded");
  await page.fill("#identifier", "01011111111");
  await page.fill("#password", "StudentPass123!@#");
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });

  await page.goto("/dashboard/playground");
  await page.waitForLoadState("domcontentloaded");
  await expect(page.getByRole("heading", { name: "محرر الكود التفاعلي" })).toBeVisible({ timeout: 15000 });

  await page.locator("select").first().selectOption("javascript");
  await page.getByRole("button", { name: /تشغيل/i }).first().click();
  await expect(page.locator("body")).toContainText(/تم التنفيذ بنجاح/, { timeout: 15000 });

  await page.screenshot({ path: "test-results/playground_repaired_desktop.png", fullPage: true });
});
