import { test, expect, type BrowserContext, type Page } from '@playwright/test'

/**
 * Happy-path E2E: Login → Recruit → Match → Chat → Close → Feedback
 *
 * Uses two independent browser contexts (user1, user2) to simulate
 * two players going through the full matching flow.
 */
test.describe.serial('Happy path: full matching flow', () => {
  let ctx1: BrowserContext
  let ctx2: BrowserContext
  let page1: Page
  let page2: Page

  // Nicknames must be <= 20 chars (input maxlength="20")
  const ts = Date.now().toString().slice(-8)
  const nick1 = `P1_${ts}`
  const nick2 = `P2_${ts}`
  let roomUrl: string

  test.beforeAll(async ({ browser }) => {
    ctx1 = await browser.newContext()
    ctx2 = await browser.newContext()
    page1 = await ctx1.newPage()
    page2 = await ctx2.newPage()
  })

  test.afterAll(async () => {
    await ctx1.close()
    await ctx2.close()
  })

  test('User1 logs in', async () => {
    await page1.goto('/')
    await page1.getByPlaceholder('ニックネーム').fill(nick1)
    await page1.getByRole('button', { name: 'はじめる' }).click()
    await expect(page1).toHaveURL(/\/lobby/)
    await expect(page1.getByText('募集一覧')).toBeVisible()
  })

  test('User1 creates a recruitment', async () => {
    await page1.getByRole('link', { name: '募集を作成' }).click()
    await expect(page1).toHaveURL(/\/recruit/)

    // Game defaults to VALORANT, region to 日本 — keep defaults
    // Start time is pre-filled +15min — keep it

    // Intercept the POST to verify the creation response
    const [response] = await Promise.all([
      page1.waitForResponse((res) => res.url().includes('/api/recruitments') && res.request().method() === 'POST'),
      page1.getByRole('button', { name: '募集する' }).click(),
    ])
    expect(response.status()).toBe(201)

    await expect(page1).toHaveURL(/\/lobby/)
    // Wait for the recruitment list to refresh and show User1's recruitment
    await expect(page1.getByRole('main').getByText(nick1)).toBeVisible({ timeout: 10_000 })
  })

  test('User2 logs in', async () => {
    await page2.goto('/')
    await page2.getByPlaceholder('ニックネーム').fill(nick2)
    await page2.getByRole('button', { name: 'はじめる' }).click()
    await expect(page2).toHaveURL(/\/lobby/)
  })

  test('User2 joins the recruitment and enters room', async () => {
    // Reload lobby to ensure fresh data, then wait for recruitment list
    await page2.reload()
    await expect(page2.getByText(nick1)).toBeVisible({ timeout: 15_000 })
    // Click the "参加する" button in the card that contains nick1
    const card = page2.locator('.bg-gray-800', { hasText: nick1 })
    await card.getByRole('button', { name: '参加する' }).click()

    // Should navigate to the room
    await expect(page2).toHaveURL(/\/room\//, { timeout: 10_000 })
    roomUrl = page2.url()

    // Room should show both members and be active
    const membersText = page2.locator('text=メンバー:')
    await expect(membersText).toContainText(nick1)
    await expect(membersText).toContainText(nick2)
    await expect(page2.getByText('アクティブ')).toBeVisible()
  })

  test('User1 navigates to the room', async () => {
    // Extract room path from user2's URL
    const roomPath = new URL(roomUrl).pathname
    await page1.goto(roomPath)

    const membersText = page1.locator('text=メンバー:')
    await expect(membersText).toContainText(nick1, { timeout: 10_000 })
    await expect(membersText).toContainText(nick2)
  })

  test('User1 sends a message', async () => {
    await page1.getByPlaceholder('メッセージを入力...').fill('こんにちは')
    await page1.getByRole('button', { name: '送信' }).click()

    // Message should appear in User1's view
    await expect(page1.getByText('こんにちは')).toBeVisible()
  })

  test('User2 sees the message and replies', async () => {
    // Wait for polling to pick up the message (polls every 3s)
    await expect(page2.getByText('こんにちは')).toBeVisible({ timeout: 10_000 })

    await page2.getByPlaceholder('メッセージを入力...').fill('よろしく')
    await page2.getByRole('button', { name: '送信' }).click()
    await expect(page2.getByText('よろしく')).toBeVisible()
  })

  test('User1 requests to close the room', async () => {
    // Verify User2's reply arrived via polling
    await expect(page1.getByText('よろしく')).toBeVisible({ timeout: 10_000 })

    // Accept the confirm dialog
    page1.once('dialog', (dialog) => dialog.accept())
    await page1.getByRole('button', { name: 'ルームを閉じる' }).click()

    // Should show pending close message (mutual close)
    await expect(page1.getByText('相手の同意を待っています')).toBeVisible({ timeout: 10_000 })
  })

  test('User2 agrees to close the room', async () => {
    // User2 should see the close button and agree
    page2.once('dialog', (dialog) => dialog.accept())
    await page2.getByRole('button', { name: 'ルームを閉じる' }).click()

    // Both agreed — room should close, User2 navigates to feedback
    await expect(page2).toHaveURL(/\/feedback/, { timeout: 10_000 })
    await expect(page2.getByText('フィードバック')).toBeVisible()
  })

  test('User1 navigates to feedback after room closes', async () => {
    // User1 should see the room is now closed (via WS or polling, 10s interval)
    await expect(page1.getByText('クローズ済み')).toBeVisible({ timeout: 15_000 })
    await page1.getByRole('link', { name: 'フィードバック' }).click()
    await expect(page1).toHaveURL(/\/feedback/)
  })

  test('User1 submits feedback', async () => {
    await page1.getByRole('button', { name: '良かった' }).click()

    await expect(page1.getByText('フィードバックを送信しました')).toBeVisible()
    await page1.getByRole('link', { name: 'ロビーに戻る' }).click()
    await expect(page1).toHaveURL(/\/lobby/)
  })

  test('User2 submits feedback', async () => {
    await page2.getByRole('button', { name: '良かった' }).click()

    await expect(page2.getByText('フィードバックを送信しました')).toBeVisible()
    await page2.getByRole('link', { name: 'ロビーに戻る' }).click()
    await expect(page2).toHaveURL(/\/lobby/)
  })
})
