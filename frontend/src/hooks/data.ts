import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { request, ApiError, type Params } from '@/api/client'
import { useSession } from './session'

export function useResource<T>(
  path: string,
  schema: z.ZodType<T>,
  params: Params = {},
  enabled = true,
) {
  const session = useSession()
  const permitted =
    session.mode === 'demo' ||
    session.capabilities.includes(
      path.includes('/monitoring/') ? 'monitoring:read' : 'security:read',
    )
  return useQuery({
    queryKey: ['api', session.epoch, session.mode, path, params],
    queryFn: ({ signal }) =>
      request(session.mode, session.credentials, path, schema, params, signal),
    enabled: enabled && session.connected && permitted,
    staleTime: 15000,
    refetchInterval: session.mode === 'live' ? 30000 : false,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    retry: (failures, error) =>
      !(error instanceof ApiError && [401, 403, 404, 409, 422, 502, 503].includes(error.status)) &&
      failures < 1,
  })
}

export function usePatch<T>(path: string, schema: z.ZodType<T>) {
  const session = useSession()
  const client = useQueryClient()
  return useMutation({
    mutationFn: (patch: unknown) =>
      request(session.mode, session.credentials, path, schema, {}, undefined, patch),
    onSuccess: () => client.invalidateQueries({ queryKey: ['api', session.epoch] }),
  })
}
