import { defineConfig, devices } from '@playwright/test';
import * as dotenv from 'dotenv';
import { loadConfig } from './src/config';

dotenv.config();

const cfg = loadConfig((process.env.PORTAL as 'admin' | 'partner' | 'customer') ?? 'admin');
const slow = !!process.env.VPN || !!process.env.SLOW_NET || cfg.timeouts.slowEnv;

export default defineConfig({
  testDir: './output/tests',
  outputDir: './output/test-results',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,

  timeout: slow ? 120_000 : 30_000,
  expect: { timeout: slow ? 30_000 : 10_000 },

  reporter: [
    ['html', { open: 'never', outputFolder: './output/playwright-report' }],
    ['list'],
  ],

  use: {
    baseURL: cfg.baseURL,
    navigationTimeout: slow ? 60_000 : 30_000,
    actionTimeout: slow ? 30_000 : 15_000,
    headless: true,
    viewport: { width: 1920, height: 1080 },
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
    video: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        ...(process.env.HTTPS_PROXY ? { proxy: { server: process.env.HTTPS_PROXY } } : {}),
      },
    },
  ],
});
