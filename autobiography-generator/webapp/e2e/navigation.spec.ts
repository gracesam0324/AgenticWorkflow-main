import { test, expect } from "@playwright/test";

test.describe("Navigation & Full Pipeline Flow", () => {
  test("can navigate from Dashboard to Interviews", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Interviews" }).click();
    await expect(page.getByTestId("interviews-title")).toBeVisible();
  });

  test("can navigate from Dashboard to Story Bible", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Story Bible" }).click();
    await expect(page.getByTestId("story-bible-title")).toBeVisible();
  });

  test("can navigate from Dashboard to Chapters", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Chapters" }).click();
    await expect(page.getByTestId("chapters-title")).toBeVisible();
  });

  test("can navigate from Dashboard to Quality", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Quality" }).click();
    await expect(page.getByTestId("quality-title")).toBeVisible();
  });

  test("back to Dashboard from any page", async ({ page }) => {
    await page.goto("/interviews");
    await page.getByRole("link", { name: "Dashboard" }).click();
    await expect(page.getByTestId("dashboard-title")).toBeVisible();
  });

  test("full pipeline walkthrough: Dashboard → Interviews → Story Bible → Chapters → Quality", async ({ page }) => {
    // Step 1: Dashboard overview
    await page.goto("/");
    await expect(page.getByTestId("dashboard-title")).toBeVisible();
    await expect(page.getByTestId("stats-grid")).toBeVisible();

    // Step 2: Review interviews
    await page.getByRole("link", { name: "Interviews" }).click();
    await expect(page.getByTestId("interviews-title")).toBeVisible();
    await expect(page.getByTestId("interview-INT-001")).toBeVisible();

    // Step 3: Check story bible
    await page.getByRole("link", { name: "Story Bible" }).click();
    await expect(page.getByTestId("story-bible-title")).toBeVisible();
    await expect(page.getByTestId("characters-card")).toBeVisible();

    // Step 4: Review chapters
    await page.getByRole("link", { name: "Chapters" }).click();
    await expect(page.getByTestId("chapters-title")).toBeVisible();

    // Step 5: Quality metrics
    await page.getByRole("link", { name: "Quality" }).click();
    await expect(page.getByTestId("quality-title")).toBeVisible();
    await expect(page.getByTestId("schemas-card")).toBeVisible();
  });
});

test.describe("API Routes", () => {
  test("GET /api/state returns pipeline state", async ({ request }) => {
    const response = await request.get("/api/state");
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty("meta");
    expect(data).toHaveProperty("interviews");
    expect(data).toHaveProperty("quality");
  });

  test("GET /api/interviews returns interview data", async ({ request }) => {
    const response = await request.get("/api/interviews");
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty("interviews");
    expect(data).toHaveProperty("count");
    expect(data.count).toBeGreaterThan(0);
  });

  test("GET /api/chapters returns chapter data", async ({ request }) => {
    const response = await request.get("/api/chapters");
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty("chapters");
    expect(data).toHaveProperty("count");
  });

  test("GET /api/quality returns quality data", async ({ request }) => {
    const response = await request.get("/api/quality");
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty("schemasCount");
  });
});
