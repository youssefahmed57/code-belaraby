import { test, expect } from "@playwright/test";

test.describe("Frontend Hash Navigation Strict Viewport & Scroll Audit", () => {

  const hashTargets = [
    { linkName: "عن المحاضر", hash: "#instructor", sectionId: "instructor", headingName: "عن المحاضر والخبرات" },
    { linkName: "باقات الأسعار", hash: "#pricing", sectionId: "pricing", headingName: "باقات الأسعار" },
    { linkName: "كيف نعمل", hash: "#how-it-works", sectionId: "how-it-works", headingName: "كيف نعمل" },
    { linkName: "الأسئلة الشائعة", hash: "#faq", sectionId: "faq", headingName: "الأسئلة الشائعة" },
    { linkName: "تواصل معنا", hash: "#contact", sectionId: "contact", headingName: "تواصل معنا" }
  ];

  for (const item of hashTargets) {
    test(`Click navbar link '${item.linkName}' scrolls to #${item.sectionId} viewport`, async ({ page }) => {
      await page.goto("/");
      await page.waitForLoadState("domcontentloaded");

      // Click exact navbar link
      const link = page.locator(`nav a[href="/${item.hash}"]`).first();
      await link.click();
      await page.waitForTimeout(1200); // Allow smooth scroll animation

      const target = page.locator(`#${item.sectionId}`);

      // 1. Verify target is in viewport
      await expect(target).toBeInViewport({ ratio: 0.3 });

      // 2. Verify unique heading is visible inside target section
      await expect(target.getByRole("heading", { name: item.headingName })).toBeVisible();

      // 3. Verify window.scrollY > 300
      const scrollY = await page.evaluate(() => window.scrollY);
      expect(scrollY).toBeGreaterThan(300);

      // 4. Verify target top is below fixed navbar (>= 70) and near top (< 220)
      const top = await target.evaluate(el => el.getBoundingClientRect().top);
      expect(top).toBeGreaterThanOrEqual(70);
      expect(top).toBeLessThan(220);

      // 5. Verify hero heading is NO LONGER in viewport
      await expect(
        page.getByRole("heading", { name: /ابدأ رحلتك في عالم البرمجة/ })
      ).not.toBeInViewport();

      // 6. Take full viewport screenshot
      await page.screenshot({ path: `test-results/hash_scroll_${item.sectionId}.png` });
    });

    test(`Direct URL load and refresh for /${item.hash}`, async ({ page }) => {
      await page.goto(`/${item.hash}`);
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(1200);

      const target = page.locator(`#${item.sectionId}`);
      await expect(target).toBeInViewport({ ratio: 0.3 });
      await expect(target.getByRole("heading", { name: item.headingName })).toBeVisible();

      const scrollY = await page.evaluate(() => window.scrollY);
      expect(scrollY).toBeGreaterThan(300);

      // Refresh page
      await page.reload();
      await page.waitForLoadState("domcontentloaded");
      await page.waitForTimeout(1200);

      await expect(target).toBeInViewport({ ratio: 0.3 });
      await expect(
        page.getByRole("heading", { name: /ابدأ رحلتك في عالم البرمجة/ })
      ).not.toBeInViewport();
    });
  }
});
