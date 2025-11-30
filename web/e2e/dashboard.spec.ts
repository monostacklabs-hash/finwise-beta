import { test, expect } from '@playwright/test'

test.describe('Dashboard E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/')
    await page.fill('input[type="email"]', 'test@example.com')
    await page.fill('input[type="password"]', 'password123')
    await page.click('button[type="submit"]')
    await page.waitForTimeout(2000)
  })

  test('should display financial health metrics', async ({ page }) => {
    // Navigate to dashboard
    await page.click('text=Dashboard')
    
    // Check for health score
    await expect(page.locator('.health-score-card')).toBeVisible()
    await expect(page.locator('.score')).toBeVisible()
    
    // Check for metrics
    await expect(page.locator('text=Net Worth')).toBeVisible()
    await expect(page.locator('text=Total Income')).toBeVisible()
    await expect(page.locator('text=Total Expenses')).toBeVisible()
  })

  test('should navigate to transactions', async ({ page }) => {
    await page.click('text=Dashboard')
    await page.click('text=📊 Transactions')
    
    await expect(page.locator('h2:has-text("Transactions")')).toBeVisible()
  })

  test('should navigate to goals', async ({ page }) => {
    await page.click('text=Dashboard')
    await page.click('text=🎯 Goals')
    
    await expect(page.locator('h2:has-text("Goals")')).toBeVisible()
  })

  test('should refresh dashboard data', async ({ page }) => {
    await page.click('text=Dashboard')
    
    // Click refresh button
    await page.click('button:has-text("Refresh")')
    
    // Wait for data to reload
    await page.waitForTimeout(1000)
    
    // Health score should still be visible
    await expect(page.locator('.health-score-card')).toBeVisible()
  })

  test('should display AI recommendations', async ({ page }) => {
    await page.click('text=Dashboard')
    
    // Check for recommendations section
    await expect(page.locator('text=AI Recommendations')).toBeVisible()
    await expect(page.locator('.recommendations-card ul')).toBeVisible()
  })
})
