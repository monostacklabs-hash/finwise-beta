import { test, expect } from '@playwright/test'

test.describe('AI Chat E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/')
    await page.fill('input[type="email"]', 'test@example.com')
    await page.fill('input[type="password"]', 'password123')
    await page.click('button[type="submit"]')
    await page.waitForTimeout(2000)
    
    // Navigate to chat
    await page.click('text=💬 AI Chat')
  })

  test('should display chat interface', async ({ page }) => {
    await expect(page.locator('h2:has-text("AI Chat")')).toBeVisible()
    await expect(page.locator('.messages')).toBeVisible()
    await expect(page.locator('.input-form')).toBeVisible()
  })

  test('should show welcome message', async ({ page }) => {
    await expect(page.locator('.welcome')).toBeVisible()
    await expect(page.locator('text=Welcome!')).toBeVisible()
  })

  test('should send message and receive response', async ({ page }) => {
    // Type message
    await page.fill('input[placeholder="Type your message..."]', 'What is my financial health?')
    
    // Send message
    await page.click('button:has-text("Send")')
    
    // Wait for response
    await page.waitForTimeout(3000)
    
    // Check user message appears
    await expect(page.locator('.message.user')).toBeVisible()
    
    // Check assistant response appears
    await expect(page.locator('.message.assistant')).toBeVisible()
  })

  test('should show typing indicator', async ({ page }) => {
    await page.fill('input[placeholder="Type your message..."]', 'Hello')
    await page.click('button:has-text("Send")')
    
    // Typing indicator should appear briefly
    await expect(page.locator('.typing')).toBeVisible({ timeout: 1000 })
  })

  test('should handle multiple messages', async ({ page }) => {
    // Send first message
    await page.fill('input[placeholder="Type your message..."]', 'I spent $50 on groceries')
    await page.click('button:has-text("Send")')
    await page.waitForTimeout(2000)
    
    // Send second message
    await page.fill('input[placeholder="Type your message..."]', 'Show my recent transactions')
    await page.click('button:has-text("Send")')
    await page.waitForTimeout(2000)
    
    // Should have multiple messages
    const messageCount = await page.locator('.message').count()
    expect(messageCount).toBeGreaterThan(2)
  })

  test('should disable send button when input is empty', async ({ page }) => {
    const sendButton = page.locator('button:has-text("Send")')
    
    // Button should be disabled when input is empty
    await expect(sendButton).toBeDisabled()
    
    // Type something
    await page.fill('input[placeholder="Type your message..."]', 'Test')
    
    // Button should be enabled
    await expect(sendButton).toBeEnabled()
  })

  test('should clear input after sending', async ({ page }) => {
    const input = page.locator('input[placeholder="Type your message..."]')
    
    await input.fill('Test message')
    await page.click('button:has-text("Send")')
    
    // Input should be cleared
    await expect(input).toHaveValue('')
  })
})
