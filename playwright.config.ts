import {defineConfig, devices} from '@playwright/test'
import {execSync} from "node:child_process";

export default defineConfig({
  testDir: './playwright/tests',
  outputDir: './playwright/results',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  timeout: 60000,
  retries: 9,
  workers: parseInt(execSync('nproc').toString()),
  use: {
    trace: 'on-first-retry'
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],
})
