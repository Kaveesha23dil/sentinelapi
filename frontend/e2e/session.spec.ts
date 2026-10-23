import { test, expect } from '@playwright/test'
import { fixtureResponse, DEMO_NOW } from '../src/api/fixtures'
import type { Alert } from '../src/api/contracts'

test('authorized investigation update uses verified capabilities and server invalidation (mock API)', async ({
  page,
}) => {
  const id = '00000000-0000-4000-8000-000000000200'
  let status = 'open'
  let patches = 0
  await page.route('**/security-api/api/v1/**', async (route) => {
    const url = new URL(route.request().url())
    const path = url.pathname.replace('/security-api', '')
    if (path.endsWith('/session')) {
      await route.fulfill({
        json: { role: 'analyst', capabilities: ['security:read', 'alerts:update'] },
      })
      return
    }
    const data = fixtureResponse(path, {
      start: '2026-10-22T12:00:00.000Z',
      end: DEMO_NOW,
      ...Object.fromEntries(url.searchParams),
    })
    if (route.request().method() === 'PATCH') {
      status = route.request().postDataJSON().status
      patches++
      await route.fulfill({ json: { ...(data as Alert), status } })
      return
    }
    await route.fulfill({ json: path.endsWith('/' + id) ? { ...(data as Alert), status } : data })
  })
  await page.goto('/alerts/' + id)
  await page.getByRole('button', { name: 'Connect backend', exact: true }).click()
  await page.getByLabel('Security credential').fill('fixture-only-not-a-real-credential')
  await page.getByRole('button', { name: 'Verify and connect' }).click()
  await expect(page.getByText('Elevated API error ratio')).toBeVisible()
  await page.getByLabel('Update status').selectOption('investigating')
  await page.getByRole('button', { name: 'Review status change' }).click()
  expect(patches).toBe(0)
  await page.getByRole('button', { name: 'Confirm update' }).click()
  await expect(page.getByText('Status saved on server.')).toBeVisible()
  expect(patches).toBe(1)
  await expect(page.getByText('investigating', { exact: true })).toBeVisible()
  expect(await page.evaluate(() => [localStorage.length, sessionStorage.length])).toEqual([0, 0])
  await page.reload()
  await expect(page.getByText('Connect to your security data')).toBeVisible()
  await page.getByRole('button', { name: 'Connect backend', exact: true }).click()
  await page.getByLabel('Security credential').fill('fixture-only-not-a-real-credential')
  await page.getByRole('button', { name: 'Verify and connect' }).click()
  await expect(page.getByText('investigating', { exact: true })).toBeVisible()
})

test('expired and forbidden responses stay explicit and never switch to demo (mock API)', async ({
  page,
}) => {
  await page.route('**/security-api/api/v1/**', async (route) => {
    if (route.request().url().endsWith('/session'))
      await route.fulfill({ json: { role: 'reader', capabilities: ['security:read'] } })
    else
      await route.fulfill({
        status: route.request().url().includes('/rules') ? 403 : 401,
        json: { detail: 'not exposed' },
      })
  })
  await page.goto('/alerts')
  await page.getByRole('button', { name: 'Connect backend', exact: true }).click()
  await page.getByLabel('Security credential').fill('fixture-only-not-a-real-credential')
  await page.getByRole('button', { name: 'Verify and connect' }).click()
  await expect(
    page.getByText('Session unauthorized. Reconnect with a valid credential.'),
  ).toBeVisible()
  await page.getByRole('link', { name: 'Detection rules', exact: true }).click()
  await expect(page.getByText('Your role does not permit this action.')).toBeVisible()
  await expect(page.getByText('DEMO DATA')).toHaveCount(0)
})
