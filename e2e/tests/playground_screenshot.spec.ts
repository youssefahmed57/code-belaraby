import { test, expect } from "@playwright/test";

test("Capture Code Playground Desktop Screenshot", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });

  // Login as seeded student
  await page.goto("/login");
  await page.waitForLoadState("domcontentloaded");
  await page.fill("#identifier", "01011111111");
  await page.fill("#password", "StudentPass123!@#");
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });

  // Navigate to playground
  await page.goto("/dashboard/playground");
  await page.waitForLoadState("domcontentloaded");
  await page.waitForFunction(() => typeof (window as any).__setPlaygroundCode === "function");

  // Click Run button
  const runBtn = page.getByRole("button", { name: /تشغيل الكود/i });
  await runBtn.click();

  // Wait for Accepted status
  await expect(page.getByText(/حالة التنفيذ:.*Accepted/)).toBeVisible({ timeout: 10000 });
  await page.waitForTimeout(1000);

  // Take screenshot
  await page.screenshot({ path: "test-results/playground_repaired_desktop.png", fullPage: true });
});
