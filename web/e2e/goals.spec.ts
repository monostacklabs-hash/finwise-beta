import { test, expect } from '@playwright/test'

test.describe('Goals E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/')
    await page.fill('input[type="email"]', 'test@example.com')
    await page.fill('input[type="password"]', 'password123')
    await page.click('button[type="submit"]')
    await page.waitForTimeout(2000)
    
    // Navigate to goals
    await page.click('text=🎯 Goals')
  })

  test('should display goals list', async ({ page }) => {
    await expect(page.locator('h2:has-text("Financial Goals")')).toBeVisible()
    await expect(page.locator('.goals-list')).toBeVisible()
  })

  test('should add new goal', async ({ page }) => {
    await page.click('button:has-text("Add Goal")')
    
    // Fill form
    await page.fill('input[placeholder*="Goal name"]', 'Emergency Fund')
    await page.fill('input[placeholder="Target amount"]', '10000')
    await page.fill('input[placeholder="Current amount"]', '2000')
    await page.fill('input[type="date"]', '2026-12-31')
    
    // Submit
    await page.click('button:has-text("Add Goal")')
    
    // Wait for goal to appear
    await page.waitForTimeout(1000)
    
    // Verify goal appears
    await expect(page.locator('text=Emergency Fund')).toBeVisible()
  })

  test('should display progress bar', async ({ page }) => {
    await page.waitForTimeout(1000)
    
    const goalCards = await page.locator('.goal-card').count()
    
    if (goalCards > 0) {
      // Check for progress bar
      await expect(page.locator('.progress-bar').first()).toBeVisible()
      await expect(page.locator('.progress-text').first()).toBeVisible()
    }
  })

  test('should update goal progress', async ({ page }) => {
    await page.waitForTimeout(1000)
    
    const goalCards = await page.locator('.goal-card').count()
    
    if (goalCards > 0) {
      // Click add progress button
      await page.click('.progress-btn:first-child')
      
      // Handle prompt
      page.on('dialog', dialog => {
        dialog.accept('500')
      })
      
      // Wait for update
      await page.waitForTimeout(1000)
    }
  })

  test('should delete goal', async ({ page }) => {
    await page.waitForTimeout(1000)
    
    const initialCount = await page.locator('.goal-card').count()
    
    if (initialCount > 0) {
      // Click delete button
      await page.click('.goal-card:first-child .delete-btn')
      
      // Confirm deletion
      page.on('dialog', dialog => dialog.accept())
      
      // Wait for deletion
      await page.waitForTimeout(1000)
      
      // Verify count decreased
      const newCount = await page.locator('.goal-card').count()
      expect(newCount).toBe(initialCount - 1)
    }
  })

  test('should show empty state when no goals', async ({ page }) => {
    // Delete all goals first (if any exist)
    await page.waitForTimeout(1000)
    
    let goalCount = await page.locator('.goal-card').count()
    
    while (goalCount > 0) {
      await page.click('.goal-card:first-child .delete-btn')
      page.on('dialog', dialog => dialog.accept())
      await page.waitForTimeout(500)
      goalCount = await page.locator('.goal-card').count()
    }
    
    // Check for empty state
    await expect(page.locator('text=No goals yet')).toBeVisible()
  })
})
