import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Explore demo' }).click()
  await expect(page.getByText('DEMO DATA')).toBeVisible()
})
test('all screens, fixture labels, accessibility and authentic captures', async ({ page }) => {
  const screens = [
    ['/', '01-dashboard-overview.png', 'Request traffic'],
    ['/traffic', '02-api-traffic.png', 'Gateway request log'],
    ['/alerts', '03-threat-alerts.png', 'Security alert queue'],
    [
      '/alerts/00000000-0000-4000-8000-000000000200',
      '04-incident-details.png',
      'Detection evidence',
    ],
    ['/rules', '05-detection-rules.png', 'Detection policies'],
    ['/ml', '06-ml-monitoring.png', 'Evaluation evidence'],
    ['/services', '07-api-services.png', 'API service inventory'],
  ]
  await page.setViewportSize({ width: 1512, height: 1100 })
  for (const [path, filename, heading] of screens) {
    await page.evaluate((path) => {
      window.history.pushState({}, '', path)
      window.dispatchEvent(new PopStateEvent('popstate'))
    }, path)
    await expect(page.getByRole('heading', { name: heading, exact: true })).toBeVisible()
    await expect(page.getByText('DEMO DATA')).toBeVisible()
    await expect(page.getByRole('status', { name: 'Loading data' })).toHaveCount(0)
    await page.screenshot({
      path: '../screenshots/08-security-dashboard/' + filename,
      fullPage: true,
    })
    const result = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze()
    expect(result.violations).toEqual([])
  }
})
test('filters, pagination, refresh and responsive layout', async ({ page }) => {
  await page.getByRole('link', { name: 'API traffic', exact: true }).click()
  await expect(page.getByText('86 records', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Next page' }).click()
  await expect(page.getByText(/Page 2 of 5/)).toBeVisible()
  await page.getByLabel('HTTP method').selectOption('POST')
  await expect(page.getByRole('button', { name: 'Next page' })).toBeDisabled()
  await page.getByRole('button', { name: 'Refresh dashboard' }).click()
  await expect(page.getByText('DEMO DATA')).toBeVisible()
  await page.setViewportSize({ width: 390, height: 844 })
  await page.getByRole('button', { name: 'Toggle navigation' }).click()
  await page.getByRole('link', { name: 'Overview', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Security overview' })).toBeVisible()
  await page.screenshot({
    path: '../screenshots/08-security-dashboard/08-responsive-dashboard.png',
    fullPage: true,
  })
  const overflow = await page.evaluate(() => ({
    width: innerWidth,
    scroll: document.documentElement.scrollWidth,
    elements: [...document.querySelectorAll('*')]
      .filter((e) => e.getBoundingClientRect().right > innerWidth + 1)
      .slice(0, 15)
      .map((e) => ({ tag: e.tagName, cls: e.className, right: e.getBoundingClientRect().right })),
  }))
  expect(overflow, JSON.stringify(overflow)).toMatchObject({ scroll: overflow.width })
})
test('demo never sends backend requests and reload does not retain credentials', async ({
  page,
}) => {
  const calls: string[] = []
  page.on('request', (r) => {
    if (r.url().includes('/api/v1/')) calls.push(r.url())
  })
  await page.getByRole('link', { name: 'Threat alerts', exact: true }).click()
  await expect(page.getByText('Security alert queue')).toBeVisible()
  expect(calls).toEqual([])
  await page.reload()
  await expect(page.getByText('Connect to your security data')).toBeVisible()
})
