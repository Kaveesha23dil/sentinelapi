import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { config, request, type Credentials, type Mode } from '@/api/client'
import { sessionSchema } from '@/api/contracts'

type Session = {
  mode: Mode
  connected: boolean
  credentials: Credentials
  capabilities: string[]
  role: string
  epoch: number
  connect: (credentials: Credentials) => Promise<void>
  demo: () => void
  disconnect: () => void
}
const SessionContext = createContext<Session | null>(null)
export function SessionProvider({ children }: { children: ReactNode }) {
  const client = useQueryClient()
  const [state, setState] = useState({
    mode: 'live' as Mode,
    connected: false,
    credentials: { monitoring: '', security: '' },
    capabilities: [] as string[],
    role: 'Disconnected',
    epoch: 0,
  })
  const reset = useCallback(() => {
    void client.cancelQueries()
    client.clear()
  }, [client])
  const connect = useCallback(
    async (credentials: Credentials) => {
      const responses = await Promise.all([
        credentials.monitoring
          ? request('live', credentials, '/api/v1/monitoring/session', sessionSchema)
          : null,
        credentials.security
          ? request('live', credentials, '/api/v1/security/session', sessionSchema)
          : null,
      ])
      if (!responses.some(Boolean)) throw new Error('Supply at least one credential')
      reset()
      setState((s) => ({
        mode: 'live',
        connected: true,
        credentials,
        capabilities: responses.flatMap((r) => r?.capabilities ?? []),
        role: responses[1]?.role ?? 'monitor',
        epoch: s.epoch + 1,
      }))
    },
    [reset],
  )
  const demo = useCallback(() => {
    if (!config.allowDemo) return
    reset()
    setState((s) => ({
      mode: 'demo',
      connected: true,
      credentials: { monitoring: '', security: '' },
      capabilities: ['monitoring:read', 'security:read'],
      role: 'Demo observer',
      epoch: s.epoch + 1,
    }))
  }, [reset])
  const disconnect = useCallback(() => {
    reset()
    setState((s) => ({
      mode: 'live',
      connected: false,
      credentials: { monitoring: '', security: '' },
      capabilities: [],
      role: 'Disconnected',
      epoch: s.epoch + 1,
    }))
  }, [reset])
  return <SessionContext value={{ ...state, connect, demo, disconnect }}>{children}</SessionContext>
}
// Shared hooks are kept next to their provider; no state is persisted.
// eslint-disable-next-line react-refresh/only-export-components
export function useSession() {
  const value = useContext(SessionContext)
  if (!value) throw new Error('Session provider required')
  return value
}
