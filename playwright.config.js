const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests-ui',
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:4174',
    channel: 'msedge',
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure'
  },
  webServer: {
    command: 'python scripts/run_ui_test_server.py',
    url: 'http://127.0.0.1:4174/api/ia/sante',
    reuseExistingServer: false,
    timeout: 30_000
  },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1440, height: 1000 } } },
    { name: 'mobile', use: { viewport: { width: 390, height: 844 } } }
  ]
});
