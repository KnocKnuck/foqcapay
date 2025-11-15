import { test, expect } from '@playwright/test';

test.describe('FOQCAPAY Trading Bot - Homepage', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the homepage before each test
    await page.goto('/');
  });

  test('should display the main title', async ({ page }) => {
    // Check that the main heading is visible
    const heading = page.locator('h1:has-text("FOQCAPAY Trading Bot")');
    await expect(heading).toBeVisible();
    await expect(heading).toContainText('🤖 FOQCAPAY Trading Bot');
  });

  test('should display subtitle', async ({ page }) => {
    // Check subtitle
    await expect(page.locator('text=Multi-Agent Crypto Trading System')).toBeVisible();
  });

  test('should display system status card', async ({ page }) => {
    // Check that system status card is present
    const statusCard = page.locator('h2:has-text("System Status")');
    await expect(statusCard).toBeVisible();
  });

  test('should connect to backend and display status', async ({ page }) => {
    // Wait for the backend connection to complete
    await page.waitForFunction(
      () => !document.body.textContent?.includes('Connecting to backend...'),
      { timeout: 10000 }
    );

    // Check that we either see success or error message
    const hasSuccess = await page.locator('text=operational').isVisible().catch(() => false);
    const hasError = await page.locator('text=Failed to connect to backend').isVisible().catch(() => false);

    expect(hasSuccess || hasError).toBeTruthy();
  });

  test('should display version information when connected', async ({ page }) => {
    // Wait for API response
    await page.waitForTimeout(2000);

    // Check if connected successfully
    const isConnected = await page.locator('text=operational').isVisible().catch(() => false);

    if (isConnected) {
      // Verify version is displayed
      await expect(page.locator('text=Version:')).toBeVisible();

      // Verify mode is displayed
      await expect(page.locator('text=Mode:')).toBeVisible();

      // Verify sprint information
      await expect(page.locator('text=Sprint:')).toBeVisible();
    }
  });

  test('should display trading pairs when connected', async ({ page }) => {
    // Wait for API response
    await page.waitForTimeout(2000);

    // Check if connected successfully
    const isConnected = await page.locator('text=operational').isVisible().catch(() => false);

    if (isConnected) {
      // Verify trading pairs section exists
      await expect(page.locator('text=Trading Pairs:')).toBeVisible();

      // Check for at least one trading pair badge
      const tradingPairs = page.locator('[class*="bg-success/10"]');
      await expect(tradingPairs.first()).toBeVisible();
    }
  });

  test('should display agent information cards', async ({ page }) => {
    // Check for the 25 Agents card
    await expect(page.locator('text=📊 25 Agents')).toBeVisible();
    await expect(page.locator('text=Specialized agents working in parallel')).toBeVisible();

    // Check for Multi-Pair card
    await expect(page.locator('text=⚡ Multi-Pair')).toBeVisible();
    await expect(page.locator('text=BTC, ETH, LINK and more')).toBeVisible();
  });

  test('should have correct page title', async ({ page }) => {
    // Check document title
    await expect(page).toHaveTitle(/FOQCAPAY/i);
  });

  test('should be responsive - mobile view', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Main title should still be visible
    await expect(page.locator('h1:has-text("FOQCAPAY Trading Bot")')).toBeVisible();

    // System status should be visible
    await expect(page.locator('h2:has-text("System Status")')).toBeVisible();
  });

  test('should be responsive - tablet view', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });

    // All main elements should be visible
    await expect(page.locator('h1:has-text("FOQCAPAY Trading Bot")')).toBeVisible();
    await expect(page.locator('h2:has-text("System Status")')).toBeVisible();
  });

  test('should handle backend connection errors gracefully', async ({ page }) => {
    // Intercept API calls and force them to fail
    await page.route('http://localhost:8000/', route => route.abort());

    // Reload the page
    await page.reload();

    // Wait for error message
    await page.waitForTimeout(2000);

    // Should show error message
    const errorMessage = page.locator('text=Failed to connect to backend');
    await expect(errorMessage).toBeVisible();

    // Should show helpful message
    await expect(page.locator('text=Make sure the backend is running')).toBeVisible();
  });

  test('should load without JavaScript errors', async ({ page }) => {
    const errors: string[] = [];

    // Listen for console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Wait for page to fully load
    await page.waitForLoadState('networkidle');

    // Filter out expected errors (like backend connection failure in test env)
    const unexpectedErrors = errors.filter(
      err => !err.includes('Failed to connect') && !err.includes('fetch')
    );

    expect(unexpectedErrors).toHaveLength(0);
  });
});
