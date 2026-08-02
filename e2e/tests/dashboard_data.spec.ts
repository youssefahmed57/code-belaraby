import { test, expect } from "@playwright/test";

test.describe("Student Dashboard Data Consistency E2E Audit", () => {

  test("Dashboard displays exact active course count, isolates demo course, and updates dynamically upon admin enrolment", async ({ page }) => {
    // 1. Authenticate as Student 1 (01011111111) who has 1 active enrolment in python-first-secondary
    const s1LoginRes = await page.request.post("/api/v1/auth/login", {
      data: { identifier: "01011111111", password: "StudentPass123!@#" }
    });
    expect(s1LoginRes.status()).toBe(200);
    const s1Auth = await s1LoginRes.json();

    await page.goto("/");
    await page.evaluate((data) => {
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_info", JSON.stringify(data.user));
    }, s1Auth);

    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");

    // 2. Summary stats top card must display "1" enrolled course
    const enrolledCountCard = page.locator('div').filter({ hasText: /^الكورسات المشترك بها$/ }).locator('..').locator('.text-2xl');
    await expect(enrolledCountCard).toHaveText("1");

    // 3. Exactly 1 active course card in "الكورسات المتاحة والمفعلة"
    const activeSection = page.locator('div.space-y-6').filter({ has: page.locator('h2:has-text("الكورسات المتاحة والمفعلة")') });
    const activeCards = activeSection.locator('h3');
    await expect(activeCards).toHaveCount(1);
    await expect(activeCards.first()).toContainText("البرمجة والذكاء الاصطناعي");

    // 4. Demo course is NOT shown as active, but displayed under "كورسات مقترحة" with "عرض تفاصيل الكورس" button
    await expect(page.locator('h2:has-text("كورسات مقترحة")')).toBeVisible();
    const suggestedBtn = page.locator('a:has-text("عرض تفاصيل الكورس")').first();
    await expect(suggestedBtn).toBeVisible();

    // 5. Direct access to unpurchased demo course/lesson is denied for Student 3 (who has no enrolments)
    const s3LoginRes = await page.request.post("/api/v1/auth/login", {
      data: { identifier: "01033333333", password: "StudentPass123!@#" }
    });
    const s3Token = (await s3LoginRes.json()).access_token;
    const deniedRes = await page.request.get("/api/v1/lessons/if-statements-and-decisions", {
      headers: { Authorization: `Bearer ${s3Token}` }
    });
    expect(deniedRes.status()).toBe(403);

    // 6. Admin activates a second enrolment for Student 1 (web-second-secondary-demo)
    const adminLoginRes = await page.request.post("/api/v1/auth/login", {
      data: { identifier: "01001340533", password: "AdminPass123!@#" }
    });
    const adminToken = (await adminLoginRes.json()).access_token;

    // Get course 2 ID
    const coursesRes = await page.request.get("/api/v1/courses");
    const courses = await coursesRes.json();
    const course2 = courses.find((c: any) => c.slug === "web-second-secondary-demo");

    // Create payment & approve to activate enrolment 2
    const orderRes = await page.request.post("/api/v1/payments/order", {
      data: { course_id: course2.id, payment_method: "instapay" },
      headers: { Authorization: `Bearer ${s1Auth.access_token}` }
    });
    const pId = (await orderRes.json()).id;

    const approveRes = await page.request.post("/api/v1/payments/admin/review", {
      data: { payment_id: pId, action: "approve", review_note: "Playwright test activation" },
      headers: { Authorization: `Bearer ${adminToken}` }
    });
    expect(approveRes.status()).toBe(200);

    // 7. Refresh Student 1 dashboard: count becomes 2 and 2 active course cards appear
    await page.reload();
    await page.waitForLoadState("domcontentloaded");
    await expect(enrolledCountCard).toHaveText("2");

    const activeCardsAfter = activeSection.locator('h3');
    await expect(activeCardsAfter).toHaveCount(2);
  });
});
