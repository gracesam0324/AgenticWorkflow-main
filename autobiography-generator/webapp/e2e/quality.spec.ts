import { test, expect } from "@playwright/test";

test.describe("Quality Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/quality");
  });

  test("renders quality title", async ({ page }) => {
    const title = page.getByTestId("quality-title");
    await expect(title).toBeVisible();
    await expect(title).toHaveText("Quality Dashboard");
  });

  test("shows pipeline quality section", async ({ page }) => {
    const section = page.getByTestId("pipeline-quality");
    await expect(section).toBeVisible();
    await expect(section).toContainText("Pipeline Quality Scores");
  });

  test("shows quality dimensions section", async ({ page }) => {
    const section = page.getByTestId("quality-dimensions");
    await expect(section).toBeVisible();
    await expect(section).toContainText("Quality Dimensions");
  });

  test("shows schemas section", async ({ page }) => {
    const section = page.getByTestId("schemas-card");
    await expect(section).toBeVisible();
    await expect(section).toContainText("JSON Schemas");
  });

  test("pipeline quality meters are present", async ({ page }) => {
    const section = page.getByTestId("pipeline-quality");
    await expect(section).toContainText("Voice Consistency");
    await expect(section).toContainText("Factual Accuracy");
    await expect(section).toContainText("Readability");
  });

  test("schemas display names", async ({ page }) => {
    // The project has JSON schemas in schemas/ directory
    const schemasCard = page.getByTestId("schemas-card");
    const schemaEntries = schemasCard.locator('[data-testid^="schema-"]');
    const count = await schemaEntries.count();
    expect(count).toBeGreaterThan(0);
  });

  test("schema shows property count", async ({ page }) => {
    const schemasCard = page.getByTestId("schemas-card");
    await expect(schemasCard).toContainText("properties");
  });
});
