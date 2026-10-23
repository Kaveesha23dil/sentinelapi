import { z } from 'zod'

export type Credentials = { monitoring: string; security: string }
export type Mode = 'live' | 'demo'
export type Params = Record<string, string | number | undefined>
declare global {
  interface Window {
    __SENTINEL_CONFIG__?: { monitoringBase: string; securityBase: string; allowDemo: boolean }
  }
}
const baseSchema = z.string().regex(/^\/[a-zA-Z0-9/_-]*$/)
export const config = z
  .object({ monitoringBase: baseSchema, securityBase: baseSchema, allowDemo: z.boolean() })
  .parse(
    window.__SENTINEL_CONFIG__ ?? {
      monitoringBase: '/monitoring-api',
      securityBase: '/security-api',
      allowDemo: false,
    },
  )
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}
export const errorMessage = (error: unknown) =>
  error instanceof ApiError
    ? ({
        401: 'Session unauthorized. Reconnect with a valid credential.',
        403: 'Your role does not permit this action.',
        404: 'This record was not found.',
        409: 'The server rejected this change. Refresh and review its current state.',
        422: 'The server rejected these filters or values.',
        503: 'This API is unavailable or not configured.',
      }[error.status] ?? 'The API request could not be completed.')
    : 'Unable to reach the API. Check the service connection and try again.'

export async function request<T>(
  mode: Mode,
  credentials: Credentials,
  path: string,
  schema: z.ZodType<T>,
  params: Params = {},
  signal?: AbortSignal,
  patch?: unknown,
): Promise<T> {
  if (mode === 'demo') {
    if (patch) throw new ApiError(403, 'Demo changes are disabled')
    const { fixtureResponse } = await import('./fixtures')
    signal?.throwIfAborted()
    return schema.parse(fixtureResponse(path, params))
  }
  const monitoring = path.startsWith('/api/v1/monitoring/')
  const credential = monitoring ? credentials.monitoring : credentials.security
  if (!credential) throw new ApiError(401, 'Credential required')
  const url = new URL(
    (monitoring ? config.monitoringBase : config.securityBase) + path,
    window.location.origin,
  )
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') url.searchParams.set(key, String(value))
  })
  let response: Response
  try {
    response = await fetch(url, {
      method: patch ? 'PATCH' : 'GET',
      signal,
      cache: 'no-store',
      credentials: 'omit',
      redirect: 'error',
      headers: {
        Authorization: `Bearer ${credential}`,
        ...(patch ? { 'Content-Type': 'application/json' } : {}),
      },
      body: patch ? JSON.stringify(patch) : undefined,
    })
  } catch (error) {
    if (signal?.aborted) throw error
    throw new ApiError(0, 'Network unavailable')
  }
  if (!response.ok) throw new ApiError(response.status, 'API request failed')
  const parsed = schema.safeParse(await response.json())
  if (!parsed.success) throw new ApiError(502, 'API response contract mismatch')
  return parsed.data
}
