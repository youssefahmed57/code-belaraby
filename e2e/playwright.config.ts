import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: "http://localhost:3000",
    channel: "chrome", // Use system installed Chrome
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
