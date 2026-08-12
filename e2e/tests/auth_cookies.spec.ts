import { expect, test } from "@playwright/test";

test.describe("Cookie Auth Regression", () => {
  test("login, reload, lesson access, logout, and admin access all use cookie session flow", async ({ browser }) => {
    test.setTimeout(60000);

    const studentContext = await browser.newContext();
    const studentPage = await studentContext.newPage();

    await studentPage.goto("/login");
    await studentPage.fill("#identifier", "01011111111");
    await studentPage.fill("#password", "StudentPass123!@#");
    await studentPage.click('button[type="submit"]');
    await expect(studentPage).toHaveURL(/\/dashboard/, { timeout: 15000 });

    await studentPage.reload();
    await expect(studentPage).toHaveURL(/\/dashboard/, { timeout: 15000 });

    await studentPage.goto("/dashboard/lessons/variables-and-data-types");
    await expect(studentPage).toHaveURL(/\/dashboard\/lessons\/variables-and-data-types/, { timeout: 15000 });
    await expect(studentPage.locator("body")).toContainText(/Variables|المتغيرات|فيديو الدرس/i, { timeout: 15000 });

    await studentPage.goto("/admin");
    await expect(studentPage.locator("#unauthorized_notice")).toBeVisible({ timeout: 15000 });

    await studentPage.goto("/");
    await studentPage.getByTitle("تسجيل الخروج").click();
    await expect(studentPage).toHaveURL(/\/login/, { timeout: 15000 });

    await studentPage.goto("/dashboard");
    await expect(studentPage).toHaveURL(/\/login/, { timeout: 15000 });

    await studentContext.close();

    const adminContext = await browser.newContext();
    const adminPage = await adminContext.newPage();
    await adminPage.goto("/login");
    await adminPage.fill("#identifier", "01001340533");
    await adminPage.fill("#password", "AdminPass123!@#");
    await adminPage.click('button[type="submit"]');
    await expect(adminPage).toHaveURL(/\/admin/, { timeout: 15000 });

    await adminPage.goto("/dashboard");
    await expect(adminPage).toHaveURL(/\/dashboard/, { timeout: 15000 });

    const csrfCookie = (await adminContext.cookies()).find((cookie) => cookie.name === "csrf_token");
    const logoutAllResponse = await adminPage.request.post("/api/v1/auth/logout-all", {
      headers: csrfCookie ? { "X-CSRF-Token": csrfCookie.value } : {},
    });
    expect(logoutAllResponse.ok()).toBeTruthy();

    await adminPage.goto("/dashboard");
    await expect(adminPage).toHaveURL(/\/login/, { timeout: 15000 });

    await adminPage.goto("/admin");
    await expect(adminPage.locator("#unauthorized_notice")).toBeVisible({ timeout: 15000 });

    await adminContext.close();
  });
});
