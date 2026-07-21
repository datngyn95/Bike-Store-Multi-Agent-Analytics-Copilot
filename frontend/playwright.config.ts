import { defineConfig, devices } from "@playwright/test";

const frontendPort = Number(process.env.PLAYWRIGHT_FRONTEND_PORT ?? 3001);
const mockApiPort = Number(process.env.PLAYWRIGHT_MOCK_API_PORT ?? 8010);
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? `http://localhost:${frontendPort}`;
const apiBaseURL = process.env.PLAYWRIGHT_API_BASE_URL ?? `http://127.0.0.1:${mockApiPort}`;
const demoUser = process.env.DASHBOARD_DEMO_USER ?? "demo";
const demoPassword = process.env.DASHBOARD_DEMO_PASSWORD ?? "demo-password";
const cookieSecret = process.env.AUTH_COOKIE_SECRET ?? "playwright-local-demo-secret";
const reuseServer = process.env.PLAYWRIGHT_REUSE_SERVER === "1";
const useManagedServers = process.env.PLAYWRIGHT_MANAGED_SERVERS === "1";
const webServer = useManagedServers
  ? undefined
  : [
      {
        name: "mock-fastapi",
        command: `node tests/e2e/mock-api-server.mjs --port ${mockApiPort}`,
        url: `${apiBaseURL}/health`,
        timeout: 30_000,
        reuseExistingServer: reuseServer,
        stdout: "pipe" as const,
        stderr: "pipe" as const
      },
      {
        name: "next-frontend",
        command: `node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port ${frontendPort}`,
        url: baseURL,
        timeout: 120_000,
        reuseExistingServer: reuseServer,
        env: {
          API_BASE_URL: apiBaseURL,
          NEXT_PUBLIC_API_BASE_URL: apiBaseURL,
          DASHBOARD_AUTH_ENABLED: "true",
          DASHBOARD_DEMO_USER: demoUser,
          DASHBOARD_DEMO_PASSWORD: demoPassword,
          AUTH_COOKIE_SECRET: cookieSecret,
          AUTH_COOKIE_SECURE: "false"
        },
        stdout: "pipe" as const,
        stderr: "pipe" as const
      }
    ];

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  expect: {
    timeout: 10_000
  },
  fullyParallel: true,
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }]
  ],
  use: {
    baseURL,
    screenshot: "only-on-failure",
    trace: "on-first-retry",
    video: "retain-on-failure"
  },
  webServer,
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] }
    },
    {
      name: "mobile-chrome",
      use: { ...devices["Pixel 7"] }
    }
  ]
});
