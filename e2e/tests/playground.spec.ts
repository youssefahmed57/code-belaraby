import { expect, test } from "@playwright/test";

test.describe("Standalone Code Playground E2E Tests", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");
    await page.fill("#identifier", "01011111111");
    await page.fill("#password", "StudentPass123!@#");
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });

    await page.goto("/dashboard/playground");
    await page.waitForLoadState("domcontentloaded");
    await expect(page.getByRole("heading", { name: "محرر الكود التفاعلي" })).toBeVisible({ timeout: 15000 });
  });

  test("1. Monaco loads, displays starter code and LTR direction, Stdin is empty", async ({ page }) => {
    const ltrContainer = page.locator('div[dir="ltr"]');
    await expect(ltrContainer.first()).toBeVisible({ timeout: 10000 });

    const stdinArea = page.locator("#stdin");
    await expect(stdinArea).toBeVisible();
    await expect(stdinArea).toHaveValue("");
  });

  test("2. Running the default Python starter code returns a success state and stdout", async ({ page }) => {
    const runBtn = page.getByRole("button", { name: /تشغيل/i }).first();
    await expect(runBtn).toBeEnabled();
    await runBtn.click();

    await expect(page.locator("body")).toContainText(/تم التنفيذ بنجاح/, { timeout: 15000 });
    await expect(page.locator("pre").first()).toContainText(/مبروك|اجتزت التحدي/, { timeout: 15000 });
  });

  test("3. Switching to JavaScript runs the default hello world sample", async ({ page }) => {
    await page.locator("select").first().selectOption("javascript");

    const runBtn = page.getByRole("button", { name: /تشغيل/i }).first();
    await runBtn.click();

    await expect(page.locator("body")).toContainText(/تم التنفيذ بنجاح/, { timeout: 15000 });
    await expect(page.locator("pre").first()).toContainText("hello world", { timeout: 15000 });
  });

  test("4. Loading a preset updates the playground and produces the expected output", async ({ page }) => {
    await page.getByRole("button", { name: "حلقة for" }).click();

    const runBtn = page.getByRole("button", { name: /تشغيل/i }).first();
    await runBtn.click();

    await expect(page.locator("body")).toContainText(/تم التنفيذ بنجاح/, { timeout: 15000 });
    await expect(page.locator("pre").first()).toContainText("المجموع النهائي = 15", { timeout: 15000 });
  });
});
