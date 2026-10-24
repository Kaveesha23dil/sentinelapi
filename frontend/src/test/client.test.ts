import { afterEach, it, expect, vi } from 'vitest'
import { request, ApiError, errorMessage } from '@/api/client'
import { sessionSchema } from '@/api/contracts'
const credentials = { monitoring: 'fixture-only-not-a-real-token', security: '' }
afterEach(() => vi.unstubAllGlobals())
it.each([401, 403, 503])('handles HTTP %s without exposing server details', async (status) => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(new Response('private server detail', { status })),
  )
  await expect(
    request('live', credentials, '/api/v1/monitoring/session', sessionSchema),
  ).rejects.toMatchObject({ status })
  expect(errorMessage(new ApiError(status, 'private server detail'))).not.toContain('private')
})
it('does not fall back to fixtures on network failure', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('network')))
  await expect(
    request('live', credentials, '/api/v1/monitoring/session', sessionSchema),
  ).rejects.toMatchObject({ status: 0 })
})
it('sends cancellation and credentials only in authorization header', async () => {
  const fetch = vi
    .fn()
    .mockResolvedValue(
      new Response(JSON.stringify({ role: 'monitor', capabilities: ['monitoring:read'] })),
    )
  vi.stubGlobal('fetch', fetch)
  const signal = new AbortController().signal
  await request('live', credentials, '/api/v1/monitoring/session', sessionSchema, {}, signal)
  expect(fetch.mock.calls[0][1]).toMatchObject({
    signal,
    credentials: 'omit',
    cache: 'no-store',
    headers: { Authorization: `Bearer ${credentials.monitoring}` },
  })
  expect(String(fetch.mock.calls[0][0])).not.toContain(credentials.monitoring)
})
it('rejects unsafe response contracts', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}')))
  await expect(
    request('live', credentials, '/api/v1/monitoring/session', sessionSchema),
  ).rejects.toMatchObject({ status: 502 })
})
it('rejects demo mutations without a network call', async () => {
  const fetch = vi.fn()
  vi.stubGlobal('fetch', fetch)
  await expect(
    request('demo', credentials, '/api/v1/security/alerts/id', sessionSchema, {}, undefined, {
      status: 'resolved',
    }),
  ).rejects.toMatchObject({ status: 403 })
  expect(fetch).not.toHaveBeenCalled()
})

it('routes security reads through the same-origin security proxy with the security credential', async () => {
  const fetch = vi
    .fn()
    .mockResolvedValue(
      new Response(JSON.stringify({ role: 'reader', capabilities: ['security:read'] })),
    )
  vi.stubGlobal('fetch', fetch)
  const pair = { monitoring: 'synthetic-monitor-only', security: 'synthetic-reader-only' }
  await request('live', pair, '/api/v1/security/session', sessionSchema)
  const [url, options] = fetch.mock.calls[0]
  expect(url.origin).toBe(window.location.origin)
  expect(url.pathname).toBe('/security-api/api/v1/security/session')
  expect(options.headers.Authorization).toBe(`Bearer ${pair.security}`)
  expect(JSON.stringify(options)).not.toContain(pair.monitoring)
})
