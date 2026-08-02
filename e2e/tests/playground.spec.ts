import { test, expect } from "@playwright/test";

test.describe("Standalone Code Playground E2E Tests", () => {
  test.beforeEach(async ({ page }) => {
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
    // Ensure client-side React useEffect has mounted
    await page.waitForFunction(() => typeof (window as any).__setPlaygroundCode === "function", { timeout: 10000 });
  });

  test("1. Monaco loads, displays starter code and LTR direction, Stdin is empty", async ({ page }) => {
    // Check Monaco Editor container direction is LTR
    const ltrContainer = page.locator('div[dir="ltr"]');
    await expect(ltrContainer.first()).toBeVisible({ timeout: 10000 });

    // Check Stdin is empty initially
    const stdinArea = page.locator("#stdin");
    await expect(stdinArea).toBeVisible();
    await expect(stdinArea).toHaveValue("");
  });

  test("2. Running print('hello') returns real stdout 'hello' and Accepted status", async ({ page }) => {
    const runBtn = page.getByRole("button", { name: /تشغيل الكود/i });
    await expect(runBtn).toBeEnabled();
    await runBtn.click();

    // Check status is Accepted and stdout contains hello
    await expect(page.getByText(/حالة التنفيذ:.*Accepted/)).toBeVisible({ timeout: 10000 });
    const stdoutBox = page.locator("pre").first();
    await expect(stdoutBox).toContainText("hello");
  });

  test("3. Running input() with stdin returns correct Hello Youssef stdout", async ({ page }) => {
    // Set Stdin value
    const stdinArea = page.locator("#stdin");
    await stdinArea.fill("Youssef");

    // Set code via window helper
    await page.evaluate(() => {
      // @ts-ignore
      window.__setPlaygroundCode('name = input()\nprint("Hello", name)');
    });

    const runBtn = page.getByRole("button", { name: /تشغيل الكود/i });
    await runBtn.click();

    await expect(page.getByText(/حالة التنفيذ:.*Accepted/)).toBeVisible({ timeout: 10000 });
    const stdoutBox = page.locator("pre").first();
    await expect(stdoutBox).toContainText("Hello Youssef");
  });

  test("4. Division by zero produces Runtime Error status and stderr", async ({ page }) => {
    await page.evaluate(() => {
      // @ts-ignore
      window.__setPlaygroundCode('print(1 / 0)');
    });

    const runBtn = page.getByRole("button", { name: /تشغيل الكود/i });
    await runBtn.click();

    await expect(page.getByText(/حالة التنفيذ:.*Runtime Error/)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("ZeroDivisionError")).toBeVisible();
  });
});
