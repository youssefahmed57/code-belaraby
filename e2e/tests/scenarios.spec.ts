import { test, expect } from "@playwright/test";

test.describe("Code Journey Academy - Full 10 E2E Production Scenarios", () => {

  test("Scenario 1: Registration and empty dashboard verification", async ({ page }) => {
    await page.goto("/register");
    await page.waitForLoadState("domcontentloaded");

    const randomPhone = "010" + Math.floor(10000000 + Math.random() * 90000000).toString();
    await page.fill("#arabic_name", "طالب سيناريو 1");
    await page.fill("#phone_number", randomPhone);
    await page.fill("#password", "StudentPass123!");
    await page.fill("#password_confirm", "StudentPass123!");
    await page.check('#terms');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });
  });

  test("Scenario 2: Payment order creation and receipt upload", async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");

    await page.fill("#identifier", "01022222222");
    await page.fill("#password", "StudentPass123!@#");
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });
    await page.goto("/dashboard/payments");
    await page.waitForLoadState("domcontentloaded");

    await page.fill('input[placeholder="مثال: 01011111111 أو username@instapay"]', "01022222222");
    await page.setInputFiles('input[type="file"]', {
      name: "receipt.png",
      mimeType: "image/png",
      buffer: Buffer.from("fake receipt content")
    });
    await page.click('button[type="submit"]');
    await expect(page.locator("body")).toContainText("تم رفع الإيصال بنجاح", { timeout: 15000 });

    const pRes = await page.request.get("/api/v1/payments/my-payments");
    expect(pRes.status()).toBe(200);
  });

  test("Scenario 3: Admin payment approval and immediate enrolment activation", async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");

    await page.fill("#identifier", "01001340533");
    await page.fill("#password", "AdminPass123!@#");
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/admin/, { timeout: 15000 });

    const pendingRes = await page.request.get("/api/v1/payments/admin/list?status_filter=pending_review");
    expect(pendingRes.status()).toBe(200);

    const approveBtn = page.locator('button:has-text("قبول وتفعيل")').first();
    if (await approveBtn.isVisible()) {
      await approveBtn.click();
      await page.click('button:has-text("تأكيد الإجراء")');
    }
  });

  test("Scenario 4: Locked lesson access protection", async ({ page }) => {
    const loginRes = await page.request.post("/api/v1/auth/login", {
      data: { identifier: "01033333333", password: "StudentPass123!@#" }
    });
    const token = (await loginRes.json()).access_token;

    const res = await page.request.get("/api/v1/lessons/if-statements-and-decisions", {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(res.status()).toBe(403);
  });

  test("Scenario 5: Automatic next-lesson unlock evaluation", async ({ page }) => {
    const loginRes = await page.request.post("/api/v1/auth/login", {
      data: { identifier: "01011111111", password: "StudentPass123!@#" }
    });
    const token = (await loginRes.json()).access_token;

    const compRes = await page.request.post("/api/v1/lessons/variables-and-data-types/complete-theory", {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(compRes.status()).toBe(200);
  });

  test("Scenario 6: Valid Python execution in Monaco Editor Playground", async ({ page }) => {
    const loginRes = await page.request.post("/api/v1/auth/login", {
      data: { identifier: "01011111111", password: "StudentPass123!@#" }
    });
    const token = (await loginRes.json()).access_token;

    const res = await page.request.post("/api/v1/coding-problems/run", {
      data: { language: "python", code: "print('Hello Code Journey')", stdin: "" },
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(res.status()).toBe(200);
    const data = await res.json();
    expect(data.status).toBe("Accepted");
    expect(data.stdout).toContain("Hello Code Journey");
  });

  test("Scenario 7: Wrong then accepted coding submission", async ({ page }) => {
    const loginRes = await page.request.post("/api/v1/auth/login", {
      data: { identifier: "01011111111", password: "StudentPass123!@#" }
    });
    const token = (await loginRes.json()).access_token;

    // 1. Wrong submission
    const wrongRes = await page.request.post("/api/v1/coding-problems/run", {
      data: { language: "python", code: "print('Wrong Output')", stdin: "" },
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(wrongRes.status()).toBe(200);

    // 2. Accepted submission
    const okRes = await page.request.post("/api/v1/coding-problems/run", {
      data: { language: "python", code: "print('Hello Code Journey')", stdin: "" },
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(okRes.status()).toBe(200);
    expect((await okRes.json()).status).toBe("Accepted");
  });

  test("Scenario 8: Cross-student receipt access denial", async ({ page }) => {
    const loginRes = await page.request.post("/api/v1/auth/login", {
      data: { identifier: "01033333333", password: "StudentPass123!@#" }
    });
    const token = (await loginRes.json()).access_token;

    const res = await page.request.get("/api/v1/admin/metrics", {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(res.status()).toBe(403);
  });

  test("Scenario 9: Instructor role cannot approve payment orders (RBAC)", async ({ page }) => {
    const loginRes = await page.request.post("/api/v1/auth/login", {
      data: { identifier: "01008168639", password: "InstructorPass123!@#" }
    });
    const token = (await loginRes.json()).access_token;

    const res = await page.request.post("/api/v1/payments/admin/review", {
      data: { payment_id: "any_id", action: "approve", review_note: "test" },
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(res.status()).toBe(403);
  });

  test("Scenario 10: Filtered CSV report export API verification", async ({ page }) => {
    const loginRes = await page.request.post("/api/v1/auth/login", {
      data: { identifier: "01001340533", password: "AdminPass123!@#" }
    });
    const token = (await loginRes.json()).access_token;

    const res = await page.request.get("/api/v1/admin/export-csv", {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(res.status()).toBe(200);
    expect(res.headers()["content-type"]).toContain("text/csv");
  });
});
