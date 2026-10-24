// Opt-in read-only live check. No traces, request headers or credential logs.
/* global localStorage, sessionStorage */
import { chromium, expect } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import console from 'node:console'
import { URL, fileURLToPath } from 'node:url'
process.chdir(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..'))
const env = Object.fromEntries(
  fs
    .readFileSync('.env', 'utf8')
    .split(/\r?\n/)
    .filter((x) => x && !x.startsWith('#') && x.includes('='))
    .map((x) => {
      const i = x.indexOf('=')
      return [x.slice(0, i), x.slice(i + 1).replace(/^["']|["']$/g, '')]
    }),
)
;(async () => {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1512, height: 1100 } })
  const responses = []
  page.on('response', (r) => {
    if (r.url().includes('/api/v1/'))
      responses.push({ path: new URL(r.url()).pathname, status: r.status() })
  })
  await page.goto(process.env.SENTINEL_FRONTEND_ORIGIN || 'http://127.0.0.1:5173')
  await page.getByRole('button', { name: 'Connect backend', exact: true }).click()
  await page.getByLabel('Monitoring credential').fill(env.MONITORING_API_TOKEN)
  await page.getByLabel('Security credential').fill(env.SECURITY_READER_TOKEN)
  await page.getByRole('button', { name: 'Verify and connect' }).click()
  await expect(page.locator('dialog')).not.toBeVisible()
  await expect(page.getByText('reader', { exact: true }).first()).toBeVisible()
  await page.getByLabel('Time range').selectOption('168')
  const screens = [
    ['Overview', 'Request traffic'],
    ['API traffic', 'Gateway request log'],
    ['Threat alerts', 'Security alert queue'],
    ['Detection rules', 'Detection policies'],
    ['ML monitoring', 'Evaluation evidence'],
    ['API services', 'API service inventory'],
  ]
  fs.mkdirSync('screenshots/dashboard-auth', { recursive: true })
  let n = 0
  for (const [label, heading] of screens) {
    await page.getByRole('link', { name: label, exact: true }).click()
    await expect(page.getByRole('heading', { name: heading, exact: true })).toBeVisible()
    await expect(page.getByRole('status', { name: 'Loading data' })).toHaveCount(0)
    await expect(page.getByText('DEMO DATA', { exact: true })).toHaveCount(0)
    const body = await page.locator('body').innerText()
    if (
      Object.values(env)
        .filter((v) => v.length >= 32)
        .some((v) => body.includes(v))
    )
      throw new Error('Private value in UI')
    await page.screenshot({ path: `screenshots/dashboard-auth/${++n}.png`, fullPage: true })
    console.log(label + ': live screen verified')
  }
  const storage = await page.evaluate(() => [localStorage.length, sessionStorage.length])
  if (storage.some(Boolean)) throw new Error('Unexpected persisted state')
  console.log('Browser API responses:', JSON.stringify(responses))
  if (
    responses.some(
      ({ path, status }) => status !== 200 && !(path.endsWith('/ml/evaluation') && status === 503),
    )
  )
    throw new Error('Unexpected live API failure')
  fs.mkdirSync('.runtime/dashboard-auth', { recursive: true })
  fs.writeFileSync(
    '.runtime/dashboard-auth/browser-results.json',
    JSON.stringify({ screens: 6, responses, storage }, null, 2),
  )
  await browser.close()
})().catch((e) => {
  let m = e.message
  for (const v of Object.values(env)) {
    if (v.length >= 12) m = m.split(v).join('[REDACTED]')
  }
  console.error(m)
  process.exit(1)
})
