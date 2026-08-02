import { test } from "@playwright/test";

test("Capture full-page desktop screenshot (1440px)", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(1000);
  await page.screenshot({ path: "test-results/homepage_desktop_1440.png", fullPage: true });
});

test("Capture full-page mobile screenshot (375px)", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/");
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(1000);
  await page.screenshot({ path: "test-results/homepage_mobile_375.png", fullPage: true });
});
