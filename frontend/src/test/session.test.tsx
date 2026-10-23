import { act, renderHook } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { afterEach, expect, it, vi } from 'vitest'
import type { ReactNode } from 'react'
import { SessionProvider, useSession } from '@/hooks/session'

afterEach(() => vi.unstubAllGlobals())

function session() {
  const client = new QueryClient()
  return renderHook(() => useSession(), {
    wrapper: ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>
        <SessionProvider>{children}</SessionProvider>
      </QueryClientProvider>
    ),
  })
}

function pendingResponse() {
  let resolve!: (response: Response) => void
  const promise = new Promise<Response>((done) => {
    resolve = done
  })
  return {
    promise,
    finish: () =>
      resolve(
        new Response(
          JSON.stringify({
            role: 'monitor',
            capabilities: ['monitoring:read'],
          }),
        ),
      ),
  }
}

it.each(['disconnect', 'demo'] as const)(
  'a pending connection cannot override %s',
  async (action) => {
    const response = pendingResponse()
    const fetch = vi.fn().mockReturnValue(response.promise)
    vi.stubGlobal('fetch', fetch)
    const { result } = session()
    let attempt!: Promise<unknown>
    act(() => {
      attempt = result.current
        .connect({ monitoring: 'fixture-token', security: '' })
        .catch((error: unknown) => error)
    })
    act(() => result.current[action]())
    expect(fetch.mock.calls[0][1].signal.aborted).toBe(true)
    await act(async () => {
      response.finish()
      expect(await attempt).toMatchObject({ name: 'AbortError' })
    })
    expect(result.current.mode).toBe(action === 'demo' ? 'demo' : 'live')
    expect(result.current.connected).toBe(action === 'demo')
    expect(result.current.credentials).toEqual({ monitoring: '', security: '' })
  },
)

it('only the newest connection attempt can establish a session', async () => {
  const first = pendingResponse()
  const second = pendingResponse()
  vi.stubGlobal(
    'fetch',
    vi.fn().mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise),
  )
  const { result } = session()
  let oldAttempt!: Promise<unknown>
  let newAttempt!: Promise<void>
  act(() => {
    oldAttempt = result.current
      .connect({ monitoring: 'old-fixture', security: '' })
      .catch((error: unknown) => error)
    newAttempt = result.current.connect({ monitoring: 'new-fixture', security: '' })
  })
  await act(async () => {
    second.finish()
    await newAttempt
  })
  await act(async () => {
    first.finish()
    await oldAttempt
  })
  expect(result.current.credentials.monitoring).toBe('new-fixture')
  expect(result.current.connected).toBe(true)
})

it('aborts connection verification when the provider unmounts', () => {
  const fetch = vi.fn().mockReturnValue(new Promise(() => {}))
  vi.stubGlobal('fetch', fetch)
  const { result, unmount } = session()
  act(() => {
    void result.current.connect({ monitoring: 'fixture-token', security: '' })
  })
  unmount()
  expect(fetch.mock.calls[0][1].signal.aborted).toBe(true)
})
