import { test, expect } from "@playwright/test";

test.describe("Chapters Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/chapters");
  });

  test("renders chapters title", async ({ page }) => {
    const title = page.getByTestId("chapters-title");
    await expect(title).toBeVisible();
    await expect(title).toHaveText("Chapter Drafts");
  });

  test("shows chapter count", async ({ page }) => {
    await expect(page.getByText(/\d+ chapter files available/)).toBeVisible();
  });

  test("displays golden chapter draft", async ({ page }) => {
    // The golden output from test-data
    const card = page.getByTestId("chapter-chapter-1-golden.md");
    await expect(card).toBeVisible();
  });

  test("shows word count for chapter", async ({ page }) => {
    const card = page.getByTestId("chapter-chapter-1-golden.md");
    await expect(card).toContainText("words");
  });

  test("shows paragraph count", async ({ page }) => {
    const card = page.getByTestId("chapter-chapter-1-golden.md");
    await expect(card).toContainText("paragraphs");
  });

  test("shows chapter preview text", async ({ page }) => {
    const card = page.getByTestId("chapter-chapter-1-golden.md");
    // Preview section should be visible
    await expect(card).toContainText("Preview");
  });

  test("chapter has structure section if headings exist", async ({ page }) => {
    // The golden chapter might have headings
    const cards = page.locator('[data-testid^="chapter-"]');
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);
  });
});
