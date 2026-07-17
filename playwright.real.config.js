const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests-ui-real',
  workers: 1,
  timeout: 180_000,
  expect: { timeout: 150_000 },
  reporter: [['list'], ['html', { outputFolder: 'playwright-report-real', open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:4175',
    channel: 'msedge',
    headless: true,
    viewport: { width: 1440, height: 1000 },
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure'
  },
  webServer: {
    command: 'python scripts/run_real_ui_test_server.py',
    url: 'http://127.0.0.1:4175/api/ia/sante',
    reuseExistingServer: false,
    timeout: 30_000
  }
});
