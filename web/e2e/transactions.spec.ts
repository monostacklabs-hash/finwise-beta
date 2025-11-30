import { test, expect } from '@playwright/test'

test.describe('Transactions E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/')
    await page.fill('input[type="email"]', 'test@example.com')
    await page.fill('input[type="password"]', 'password123')
    await page.click('button[type="submit"]')
    await page.waitForTimeout(2000)
    
    // Navigate to transactions
    await page.click('text=💰 Transactions')
  })

  test('should display transactions list', async ({ page }) => {
    await expect(page.locator('h2:has-text("Transactions")')).toBeVisible()
    await expect(page.locator('.transactions-list')).toBeVisible()
  })

  test('should add new expense transaction', async ({ page }) => {
    // Click add button
    await page.click('button:has-text("Add Transaction")')
    
    // Fill form
    await page.selectOption('select', 'expense')
    await page.fill('input[placeholder="Amount"]', '50.00')
    await page.fill('input[placeholder*="Category"]', 'groceries')
    await page.fill('input[placeholder="Description"]', 'Weekly shopping')
    
    // Submit
    await page.click('button:has-text("Add Transaction")')
    
    // Wait for transaction to appear
    await page.waitForTimeout(1000)
    
    // Verify transaction appears in list
    await expect(page.locator('text=Weekly shopping')).toBeVisible()
  })

  test('should add new income transaction', async ({ page }) => {
    await page.click('button:has-text("Add Transaction")')
    
    await page.selectOption('select', 'income')
    await page.fill('input[placeholder="Amount"]', '5000.00')
    await page.fill('input[placeholder*="Category"]', 'salary')
    await page.fill('input[placeholder="Description"]', 'Monthly salary')
    
    await page.click('button:has-text("Add Transaction")')
    
    await page.waitForTimeout(1000)
    await expect(page.locator('text=Monthly salary')).toBeVisible()
  })

  test('should delete transaction', async ({ page }) => {
    // Wait for transactions to load
    await page.waitForTimeout(1000)
    
    // Get initial count
    const initialCount = await page.locator('.transaction-item').count()
    
    if (initialCount > 0) {
      // Click first delete button
      await page.click('.transaction-item:first-child .delete-btn')
      
      // Confirm deletion
      page.on('dialog', dialog => dialog.accept())
      
      // Wait for deletion
      await page.waitForTimeout(1000)
      
      // Verify count decreased
      const newCount = await page.locator('.transaction-item').count()
      expect(newCount).toBe(initialCount - 1)
    }
  })

  test('should cancel add transaction', async ({ page }) => {
    await page.click('button:has-text("Add Transaction")')
    
    // Form should be visible
    await expect(page.locator('.add-form')).toBeVisible()
    
    // Click cancel
    await page.click('button:has-text("Cancel")')
    
    // Form should be hidden
    await expect(page.locator('.add-form')).not.toBeVisible()
  })
})
