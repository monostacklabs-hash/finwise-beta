import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test('should register new user', async ({ page }) => {
    await page.goto('/')
    
    // Click register tab
    await page.click('text=Register')
    
    // Fill registration form
    await page.fill('input[type="text"]', 'Test User')
    await page.fill('input[type="email"]', `test${Date.now()}@example.com`)
    await page.fill('input[type="password"]', 'password123')
    
    // Submit form
    await page.click('button[type="submit"]')
    
    // Should redirect to dashboard
    await expect(page.locator('text=Financial Dashboard')).toBeVisible({ timeout: 10000 })
  })

  test('should login existing user', async ({ page }) => {
    await page.goto('/')
    
    // Fill login form (assuming test user exists)
    await page.fill('input[type="email"]', 'test@example.com')
    await page.fill('input[type="password"]', 'password123')
    
    // Submit form
    await page.click('button[type="submit"]')
    
    // Should show dashboard or error
    await page.waitForTimeout(2000)
  })

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/')
    
    await page.fill('input[type="email"]', 'invalid@example.com')
    await page.fill('input[type="password"]', 'wrongpassword')
    
    await page.click('button[type="submit"]')
    
    // Should show error message
    await expect(page.locator('.error')).toBeVisible({ timeout: 5000 })
  })

  test('should logout user', async ({ page, context }) => {
    // Set auth token
    await context.addCookies([{
      name: 'token',
      value: 'test-token',
      domain: 'localhost',
      path: '/',
    }])
    
    await page.goto('/')
    
    // Click logout
    await page.click('text=Logout')
    
    // Should redirect to login
    await expect(page.locator('text=Login')).toBeVisible()
  })
})
