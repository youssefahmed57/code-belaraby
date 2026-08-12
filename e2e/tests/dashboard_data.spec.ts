import { expect, request as pwRequest, test } from "@playwright/test";

async function createReviewedPayment(
  studentRequest: Awaited<ReturnType<typeof pwRequest.newContext>>,
  adminRequest: Awaited<ReturnType<typeof pwRequest.newContext>>,
  studentToken: string,
  adminToken: string,
  courseId: string,
  senderIdentifier: string,
) {
  const orderResponse = await studentRequest.post("/api/v1/payments/order", {
    data: { course_id: courseId, payment_method: "instapay" },
    headers: { Authorization: `Bearer ${studentToken}` },
  });
  expect(orderResponse.ok()).toBeTruthy();
  const order = await orderResponse.json();
  const submittedAmount = String(order.amount_expected ?? "0");

  const uploadResponse = await studentRequest.post("/api/v1/payments/upload-receipt", {
    headers: { Authorization: `Bearer ${studentToken}` },
    multipart: {
      payment_id: order.id,
      sender_identifier: senderIdentifier,
      amount_submitted: submittedAmount,
      file: {
        name: "receipt.png",
        mimeType: "image/png",
        buffer: Buffer.concat([
          Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
          Buffer.from(`e2e-receipt-${Date.now()}-${Math.random()}`),
        ]),
      },
    },
  });
  expect(uploadResponse.ok()).toBeTruthy();

  const reviewResponse = await adminRequest.post("/api/v1/payments/admin/review", {
    data: {
      payment_id: order.id,
      action: "approve",
      review_note: "E2E approval",
    },
    headers: { Authorization: `Bearer ${adminToken}` },
  });
  expect(reviewResponse.ok()).toBeTruthy();
}

test.describe("Student Dashboard Data Consistency E2E Audit", () => {
  test("Dashboard displays exact active course count, isolates demo course, and updates dynamically upon admin enrolment", async ({ page }) => {
    const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:3000";
    const randPhone = `010${Math.floor(10000000 + Math.random() * 90000000)}`;

    const registerResponse = await page.request.post("/api/v1/auth/register", {
      data: {
        arabic_name: "طالب لوحة التحكم E2E",
        phone_number: randPhone,
        password: "StudentPass123!@#",
        password_confirm: "StudentPass123!@#",
        grade_level: "first_secondary",
      },
    });
    expect(registerResponse.ok()).toBeTruthy();
    const studentAuth = await registerResponse.json();

    const adminRequest = await pwRequest.newContext({ baseURL });
    const adminLoginResponse = await adminRequest.post("/api/v1/auth/login", {
      data: { identifier: "01001340533", password: "AdminPass123!@#" },
    });
    expect(adminLoginResponse.ok()).toBeTruthy();
    const adminAuth = await adminLoginResponse.json();

    const coursesResponse = await page.request.get("/api/v1/courses");
    expect(coursesResponse.ok()).toBeTruthy();
    const courses = await coursesResponse.json();
    const course1 = courses.find((course: any) => course.slug === "python-first-secondary");
    const course2 = courses.find((course: any) => course.slug === "web-second-secondary-demo");
    expect(course1).toBeTruthy();
    expect(course2).toBeTruthy();

    await createReviewedPayment(page.request, adminRequest, studentAuth.access_token, adminAuth.access_token, course1.id, randPhone);

    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });

    const summaryAfterFirstResponse = await page.request.get("/api/v1/dashboard/summary", {
      headers: { Authorization: `Bearer ${studentAuth.access_token}` },
    });
    expect(summaryAfterFirstResponse.ok()).toBeTruthy();
    const summaryAfterFirst = await summaryAfterFirstResponse.json();
    expect(summaryAfterFirst.active_enrolment_count).toBe(1);

    await expect(page.locator("body")).toContainText(course1.title);
    await expect(page.getByRole("link", { name: "متابعة التعلم" })).toHaveCount(1);
    await expect(page.locator("body")).toContainText("كورسات مقترحة");

    await createReviewedPayment(page.request, adminRequest, studentAuth.access_token, adminAuth.access_token, course2.id, `${randPhone}-2`);

    await page.reload();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });

    const summaryAfterSecondResponse = await page.request.get("/api/v1/dashboard/summary", {
      headers: { Authorization: `Bearer ${studentAuth.access_token}` },
    });
    expect(summaryAfterSecondResponse.ok()).toBeTruthy();
    const summaryAfterSecond = await summaryAfterSecondResponse.json();
    expect(summaryAfterSecond.active_enrolment_count).toBe(2);

    await expect(page.locator("body")).toContainText(course2.title);
    await expect(page.getByRole("link", { name: "متابعة التعلم" })).toHaveCount(2);

    await adminRequest.dispose();
  });
});
