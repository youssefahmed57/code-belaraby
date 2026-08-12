import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:3000",
    channel: "chrome",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chrome",
      use: {
        channel: "chrome",
      },
    },
  ],
});
