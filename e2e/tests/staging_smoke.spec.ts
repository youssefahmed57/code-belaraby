import { test, expect } from "@playwright/test";

test.describe("Staging Smoke Tests Suite", () => {

  test("1. Homepage loads successfully with hero section and titles", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");
    await expect(page).toHaveTitle(/كود جيرني/);
    await expect(page.locator("h1")).toBeVisible();
  });

  test("2. Health and Ready API probes return 200 OK", async ({ request }) => {
    const healthRes = await request.get("/api/v1/health");
    expect(healthRes.status()).toBe(200);
    const healthJson = await healthRes.json();
    expect(healthJson.status).toBe("healthy");

    const readyRes = await request.get("/api/v1/ready");
    expect(readyRes.status()).toBe(200);
    const readyJson = await readyRes.json();
    expect(readyJson.status).toBe("ready");
  });

  test("3. Student Login and Dashboard loading", async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");

    await page.fill("#identifier", "01011111111");
    await page.fill("#password", "StudentPass123!@#");
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });
    await expect(page.locator('h1:has-text("أهلاً بك")')).toBeVisible();
  });

  test("4. Prevent Admin Access for Student Role", async ({ page }) => {
    await page.goto("/login");
    await page.fill("#identifier", "01011111111");
    await page.fill("#password", "StudentPass123!@#");
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);

    // Direct navigation to /admin displays Unauthorized notice
    await page.goto("/admin");
    await expect(page.locator("#unauthorized_notice")).toBeVisible();
  });

  test("5. Sandbox Code Execution endpoint returns stdout", async ({ request }) => {
    // Login as student to get token
    const loginRes = await request.post("/api/v1/auth/login", {
      data: { identifier: "01011111111", password: "StudentPass123!@#" }
    });
    expect(loginRes.status()).toBe(200);
    const token = (await loginRes.json()).access_token;

    const execRes = await request.post("/api/v1/coding-problems/run", {
      data: { language: "python", code: "print('Staging Smoke Test')", stdin: "" },
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(execRes.status()).toBe(200);
    const execJson = await execRes.json();
    expect(execJson.status).toBe("Accepted");
    expect(execJson.stdout.trim()).toBe("Staging Smoke Test");
  });

  test("6. Student Progress Retention & Summary Endpoint", async ({ request }) => {
    const loginRes = await request.post("/api/v1/auth/login", {
      data: { identifier: "01011111111", password: "StudentPass123!@#" }
    });
    const token = (await loginRes.json()).access_token;

    const summaryRes = await request.get("/api/v1/dashboard/summary", {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(summaryRes.status()).toBe(200);
    const data = await summaryRes.json();
    expect(data.active_enrolment_count).toBeGreaterThanOrEqual(1);
  });

});
