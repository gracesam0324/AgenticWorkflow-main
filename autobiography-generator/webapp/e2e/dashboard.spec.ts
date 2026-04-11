import { test, expect } from "@playwright/test";

test.describe("Dashboard Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("renders dashboard title", async ({ page }) => {
    const title = page.getByTestId("dashboard-title");
    await expect(title).toBeVisible();
    await expect(title).toHaveText("Pipeline Dashboard");
  });

  test("shows current phase card", async ({ page }) => {
    const phaseCard = page.getByTestId("phase-card");
    await expect(phaseCard).toBeVisible();
    // Should contain "Current Phase" text
    await expect(phaseCard).toContainText("Current Phase");
  });

  test("displays phase badge", async ({ page }) => {
    const badge = page.getByTestId("phase-badge");
    await expect(badge).toBeVisible();
  });

  test("renders stats grid with 4 cards", async ({ page }) => {
    const grid = page.getByTestId("stats-grid");
    await expect(grid).toBeVisible();

    // Check individual stat cards
    await expect(page.getByTestId("stat-interviews")).toBeVisible();
    await expect(page.getByTestId("stat-target-chapters")).toBeVisible();
    await expect(page.getByTestId("stat-word-target")).toBeVisible();
    await expect(page.getByTestId("stat-schemas")).toBeVisible();
  });

  test("shows quality card", async ({ page }) => {
    const qualityCard = page.getByTestId("quality-card");
    await expect(qualityCard).toBeVisible();
    await expect(qualityCard).toContainText("Quality Metrics");
  });

  test("shows available data card", async ({ page }) => {
    const dataCard = page.getByTestId("data-card");
    await expect(dataCard).toBeVisible();
    await expect(dataCard).toContainText("Available Data");
  });

  test("shows interviews preview section", async ({ page }) => {
    const preview = page.getByTestId("interviews-preview");
    await expect(preview).toBeVisible();
    await expect(preview).toContainText("Recent Interviews");
  });

  test("navigation links are present", async ({ page }) => {
    const nav = page.locator("nav");
    await expect(nav).toBeVisible();
    await expect(nav.getByRole("link", { name: "Dashboard" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Interviews" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Story Bible" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Chapters" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Quality" })).toBeVisible();
  });

  test("branding is visible", async ({ page }) => {
    await expect(page.getByText("AutoBiography", { exact: true })).toBeVisible();
    const nav = page.locator("nav");
    await expect(nav.getByText("Pipeline Dashboard")).toBeVisible();
  });
});
