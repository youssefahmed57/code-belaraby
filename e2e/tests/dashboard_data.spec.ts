import { test, expect, request as pwRequest } from "@playwright/test";

test.describe("Student Dashboard Data Consistency E2E Audit", () => {

  test("Dashboard displays exact active course count, isolates demo course, and updates dynamically upon admin enrolment", async ({ page }) => {
    // 1. Register a fresh student for idempotent test execution
    const randPhone = `010${Math.floor(10000000 + Math.random() * 90000000)}`;
    const regRes = await page.request.post("/api/v1/auth/register", {
      data: {
        arabic_name: "طالب لوحة التحكم E2E",
        phone_number: randPhone,
        password: "StudentPass123!@#",
        password_confirm: "StudentPass123!@#",
        grade_level: "first_secondary"
      }
    });
    expect(regRes.status()).toBe(200);
    const auth = await regRes.json();

    // Admin Token for activating enrolments using isolated request context to prevent cookie contamination
    const adminContext = await pwRequest.newContext({ baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000" });
    const adminLoginRes = await adminContext.post("/api/v1/auth/login", {
      data: { identifier: "01001340533", password: "AdminPass123!@#" }
    });
    const adminToken = (await adminLoginRes.json()).access_token;

    // Get course 1 ID (python-first-secondary)
    const coursesRes = await page.request.get("/api/v1/courses");
    const courses = await coursesRes.json();
    const course1 = courses.find((c: any) => c.slug === "python-first-secondary");
    const course2 = courses.find((c: any) => c.slug === "web-second-secondary-demo");

    // Activate course 1 for this student
    const order1Res = await page.request.post("/api/v1/payments/order", {
      data: { course_id: course1.id, payment_method: "instapay" },
      headers: { Authorization: `Bearer ${auth.access_token}` }
    });
    const p1Id = (await order1Res.json()).id;
    await adminContext.post("/api/v1/payments/admin/review", {
      data: { payment_id: p1Id, action: "approve", review_note: "Initial activation" },
      headers: { Authorization: `Bearer ${adminToken}` }
    });

    // 2. Set student session and load /dashboard
    await page.goto("/");
    await page.evaluate((data) => {
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_info", JSON.stringify(data.user));
    }, auth);

    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");

    // 3. Summary stats top card must display "1" enrolled course
    const enrolledCountCard = page.locator('div').filter({ hasText: /^الكورسات المشترك بها$/ }).locator('..').locator('.text-2xl');
    await expect(enrolledCountCard).toHaveText("1");

    // 4. Exactly 1 active course card in "الكورسات المتاحة والمفعلة"
    const activeSection = page.locator('div.space-y-6').filter({ has: page.locator('h2:has-text("الكورسات المتاحة والمفعلة")') });
    const activeCards = activeSection.locator('h3');
    await expect(activeCards).toHaveCount(1);

    // 5. Unpurchased demo course is NOT shown as active, but displayed under "كورسات مقترحة"
    await expect(page.locator('h2:has-text("كورسات مقترحة")')).toBeVisible();

    // 6. Admin approves second course enrolment
    const order2Res = await page.request.post("/api/v1/payments/order", {
      data: { course_id: course2.id, payment_method: "instapay" },
      headers: { Authorization: `Bearer ${auth.access_token}` }
    });
    const p2Id = (await order2Res.json()).id;

    await adminContext.post("/api/v1/payments/admin/review", {
      data: { payment_id: p2Id, action: "approve", review_note: "Second activation" },
      headers: { Authorization: `Bearer ${adminToken}` }
    });

    // 7. Refresh student dashboard: count becomes 2 and 2 active course cards appear
    await page.reload();
    await page.waitForLoadState("domcontentloaded");
    await expect(enrolledCountCard).toHaveText("2");

    const activeCardsAfter = activeSection.locator('h3');
    await expect(activeCardsAfter).toHaveCount(2);
  });
});
