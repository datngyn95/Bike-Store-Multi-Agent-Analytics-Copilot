import { expect, test } from "@playwright/test";

const demoUser = process.env.DASHBOARD_DEMO_USER ?? "demo";
const demoPassword = process.env.DASHBOARD_DEMO_PASSWORD ?? "demo-password";

async function login(page: import("@playwright/test").Page) {
  await page.goto("/");
  await expect(page).toHaveURL(/\/login$/);
  await page.locator('input[name="username"]').fill(demoUser);
  await page.locator('input[name="password"]').fill(demoPassword);
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(/\/$/);
}

test("auth gate protects the executive dashboard and renders KPI evidence", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/login$/);

  await login(page);

  await expect(page.locator(".brand")).toContainText("Bike Store");
  await expect(page.locator(".page-title")).toContainText("Bike Store");
  await expect(page.locator(".metric-card").first()).toContainText(/US\$|\$/);
  await expect(page.locator(".source-pill").first()).toContainText("analytics.mart_executive_summary");
  await expect(page.locator("table").first()).toContainText("Trek Slash");
});

test("sales page supports the year filter used in the demo", async ({ page }) => {
  await login(page);

  await page.getByRole("link", { name: /Ban hang|Bán hàng/i }).click();
  await expect(page).toHaveURL(/\/sales$/);

  await page.getByRole("link", { name: "2017" }).click();
  await expect(page).toHaveURL(/\/sales\?year=2017$/);
  await expect(page.locator(".source-pill").first()).toContainText("analytics.mart_sales_monthly");
  await expect(page.locator("table").first()).toContainText(/2017|17/);
});

test("copilot flow returns routed agents, guarded SQL and result rows", async ({ page }) => {
  await login(page);

  await page.goto("/copilot");
  await page.locator('textarea[name="q"]').fill("Cua hang nao co doanh thu cao nhat?");
  await page.locator('form[action="/copilot"] button[type="submit"]').click();

  await expect(page).toHaveURL(/\/copilot\?q=/);
  await expect(page.locator(".answer")).toContainText("Baldwin Bikes");
  await expect(page.locator(".pill-list")).toContainText("store_agent");
  await expect(page.locator(".pill-list")).toContainText("sales_agent");
  await expect(page.locator(".sql-block")).toContainText("analytics.mart_sales_by_store");
  await expect(page.locator("table").first()).toContainText("Baldwin Bikes");
});
