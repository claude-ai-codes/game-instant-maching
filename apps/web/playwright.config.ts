import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },
  ],
  webServer: [
    {
      command: 'uv run uvicorn app.main:app --host 0.0.0.0 --port 8000',
      cwd: '../api',
      port: 8000,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
    {
      command: 'pnpm dev',
      port: 5173,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
      env: {
        PATH: `${process.env.HOME}/.npm-global/bin:${process.env.PATH}`,
      },
    },
  ],
})
