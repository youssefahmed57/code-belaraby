import { test, expect } from "@playwright/test";

test("Capture Student Dashboard Desktop and Mobile Screenshots", async ({ page }) => {
  const loginRes = await page.request.post("/api/v1/auth/login", {
    data: { identifier: "01011111111", password: "StudentPass123!@#" }
  });
  const auth = await loginRes.json();

  await page.goto("/");
  await page.evaluate((data) => {
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("user_info", JSON.stringify(data.user));
  }, auth);

  // Desktop Screenshot (1440px)
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/dashboard");
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(1000);
  await page.screenshot({ path: "test-results/dashboard_repaired_desktop.png", fullPage: true });

  // Mobile Screenshot (375px)
  await page.setViewportSize({ width: 375, height: 812 });
  await page.reload();
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(1000);
  await page.screenshot({ path: "test-results/dashboard_repaired_mobile.png", fullPage: true });
});
