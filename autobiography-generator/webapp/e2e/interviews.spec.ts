import { test, expect } from "@playwright/test";

test.describe("Interviews Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/interviews");
  });

  test("renders interviews title", async ({ page }) => {
    const title = page.getByTestId("interviews-title");
    await expect(title).toBeVisible();
    await expect(title).toHaveText("Interview Transcripts");
  });

  test("shows interview count in subtitle", async ({ page }) => {
    await expect(page.getByText(/\d+ interview sessions available/)).toBeVisible();
  });

  test("displays INT-001 interview card", async ({ page }) => {
    const card = page.getByTestId("interview-INT-001");
    await expect(card).toBeVisible();
  });

  test("INT-001 shows session metadata", async ({ page }) => {
    const card = page.getByTestId("interview-INT-001");
    await expect(card).toContainText("INT-001");
    await expect(card).toContainText("Childhood in Busan");
    await expect(card).toContainText("Park Jimin");
    await expect(card).toContainText("reflective");
  });

  test("INT-001 shows theme tags", async ({ page }) => {
    const card = page.getByTestId("interview-INT-001");
    await expect(card).toContainText("family");
    await expect(card).toContainText("education");
  });

  test("INT-001 shows segments", async ({ page }) => {
    const card = page.getByTestId("interview-INT-001");
    // Segment topics should be visible
    await expect(card).toContainText("Family home and neighborhood");
    await expect(card).toContainText("School experiences and friendships");
    await expect(card).toContainText("Father's shop and life lessons");
  });

  test("INT-001 shows key quotes", async ({ page }) => {
    const card = page.getByTestId("interview-INT-001");
    await expect(card).toContainText("fisherman at heart");
  });

  test("INT-001 shows emotional markers", async ({ page }) => {
    const card = page.getByTestId("interview-INT-001");
    await expect(card).toContainText("nostalgia");
  });

  test("INT-001 shows people mentioned", async ({ page }) => {
    const card = page.getByTestId("interview-INT-001");
    await expect(card).toContainText("Park Jihoon");
    await expect(card).toContainText("older brother");
  });

  test("displays INT-002 interview card", async ({ page }) => {
    const card = page.getByTestId("interview-INT-002");
    await expect(card).toBeVisible();
  });

  test("multiple interviews are displayed", async ({ page }) => {
    const cards = page.locator('[data-testid^="interview-INT-"]');
    await expect(cards).toHaveCount(2);
  });
});
