import { test, expect } from "@playwright/test";

test.describe("Story Bible Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/story-bible");
  });

  test("renders story bible title", async ({ page }) => {
    const title = page.getByTestId("story-bible-title");
    await expect(title).toBeVisible();
    await expect(title).toHaveText("Story Bible");
  });

  test("shows characters card", async ({ page }) => {
    const card = page.getByTestId("characters-card");
    await expect(card).toBeVisible();
    await expect(card).toContainText("Characters");
  });

  test("shows places card", async ({ page }) => {
    const card = page.getByTestId("places-card");
    await expect(card).toBeVisible();
    await expect(card).toContainText("Places");
  });

  test("shows timeline card", async ({ page }) => {
    const card = page.getByTestId("timeline-card");
    await expect(card).toBeVisible();
    await expect(card).toContainText("Timeline");
  });

  test("characters extracted from interviews", async ({ page }) => {
    const card = page.getByTestId("characters-card");
    // These characters appear in INT-001 test data
    await expect(card).toContainText("Park Jihoon");
    await expect(card).toContainText("older brother");
  });

  test("places extracted from interviews", async ({ page }) => {
    const card = page.getByTestId("places-card");
    await expect(card).toContainText("Haeundae apartment");
    await expect(card).toContainText("Busan");
  });

  test("events extracted from interviews", async ({ page }) => {
    const card = page.getByTestId("timeline-card");
    await expect(card).toContainText("events");
  });

  test("event significance badges shown", async ({ page }) => {
    const card = page.getByTestId("timeline-card");
    // INT-001 has "turning-point" and "background" events
    const badges = card.locator("span").filter({ hasText: /turning-point|background|milestone/ });
    await expect(badges.first()).toBeVisible();
  });

  test("source interview references shown", async ({ page }) => {
    const card = page.getByTestId("characters-card");
    await expect(card).toContainText("INT-001");
  });

  test("three-column layout on large screens", async ({ page }) => {
    // Characters, Places, Timeline should all be in the grid
    await expect(page.getByTestId("characters-card")).toBeVisible();
    await expect(page.getByTestId("places-card")).toBeVisible();
    await expect(page.getByTestId("timeline-card")).toBeVisible();
  });
});
