import { expect, test } from "@playwright/test";

test.describe("Password reset and payment hardening flows", () => {
  test("forgot password shows generic success and reset password handles invalid token", async ({ page }) => {
    await page.goto("/forgot-password");
    await page.fill("#forgot_identifier", "student1@codejourney.eg");
    await page.click('button[type="submit"]');

    await expect(page.locator("body")).toContainText("إذا كان البريد الإلكتروني أو رقم الهاتف مسجلاً لدينا", {
      timeout: 15000,
    });
    await expect(page.locator("body")).not.toContainText("reset_token");

    await page.goto("/reset-password?token=invalid-token");
    await page.fill("#reset_password", "ValidPass123");
    await page.fill("#reset_password_confirm", "ValidPass123");
    await page.click('button[type="submit"]');

    await expect(page.locator("body")).toContainText(/غير صالح|منتهي الصلاحية|تعذر/i, { timeout: 15000 });
  });

  test("payment upload retry reuses the same pending order after a failed oversized receipt", async ({ page }) => {
    const randomPhone = `010${Math.floor(10000000 + Math.random() * 90000000)}`;

    await page.goto("/register");
    await page.fill("#arabic_name", "طالب إعادة رفع الإيصال");
    await page.fill("#phone_number", randomPhone);
    await page.fill("#password", "StudentPass123");
    await page.fill("#password_confirm", "StudentPass123");
    await page.check("#terms");
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });

    await page.goto("/dashboard/payments");
    await expect(page.locator("select").first()).not.toHaveValue("", { timeout: 15000 });
    await page.fill('input[placeholder="مثال: 01011111111 أو username@instapay"]', randomPhone);

    const oversizedReceipt = Buffer.concat([
      Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
      Buffer.alloc(5 * 1024 * 1024 + 128, 0x61),
    ]);
    await page.setInputFiles('input[type="file"]', {
      name: "oversized-receipt.png",
      mimeType: "image/png",
      buffer: oversizedReceipt,
    });
    await page.click('button[type="submit"]');
    await expect(page.locator("body")).toContainText("5 ميجابايت", { timeout: 15000 });
    await expect(page.locator("button[type='submit']")).toContainText("إعادة رفع الإيصال", { timeout: 15000 });

    const paymentsAfterFailure = await page.request.get("/api/v1/payments/my-payments");
    expect(paymentsAfterFailure.status()).toBe(200);
    const failedList = await paymentsAfterFailure.json();
    expect(failedList.length).toBe(1);
    expect(["draft", "awaiting_receipt", "more_info_required"]).toContain(failedList[0].status);

    await page.setInputFiles('input[type="file"]', {
      name: "receipt.png",
      mimeType: "image/png",
      buffer: Buffer.concat([
        Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
        Buffer.from(`valid-retry-receipt-${Date.now()}`),
      ]),
    });
    await page.click('button[type="submit"]');
    await expect(page.locator("body")).toContainText("تم رفع الإيصال بنجاح", { timeout: 15000 });

    const paymentsAfterSuccess = await page.request.get("/api/v1/payments/my-payments");
    expect(paymentsAfterSuccess.status()).toBe(200);
    const successfulList = await paymentsAfterSuccess.json();
    expect(successfulList.length).toBe(1);
    expect(successfulList[0].status).toBe("pending_review");
  });
});
