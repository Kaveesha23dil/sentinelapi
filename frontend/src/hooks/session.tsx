import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  useEffect,
  type ReactNode,
} from 'react'
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
  cancelConnect: () => void
  demo: () => void
  disconnect: () => void
}
const SessionContext = createContext<Session | null>(null)
export function SessionProvider({ children }: { children: ReactNode }) {
  const client = useQueryClient()
  const connection = useRef<AbortController | null>(null)
  useEffect(() => () => connection.current?.abort(), [])
  const cancelConnect = useCallback(() => {
    connection.current?.abort()
    connection.current = null
  }, [])
  const [state, setState] = useState({
    mode: 'live' as Mode,
    connected: false,
    credentials: { monitoring: '', security: '' },
    capabilities: [] as string[],
    role: 'Disconnected',
    epoch: 0,
  })
  const reset = useCallback(() => {
    connection.current?.abort()
    connection.current = null
    void client.cancelQueries()
    client.clear()
  }, [client])
  const connect = useCallback(
    async (credentials: Credentials) => {
      connection.current?.abort()
      const controller = new AbortController()
      connection.current = controller
      // Snapshot the caller's credentials for this verification attempt.
      credentials = { ...credentials }
      const responses = await Promise.all([
        credentials.monitoring
          ? request(
              'live',
              credentials,
              '/api/v1/monitoring/session',
              sessionSchema,
              {},
              controller.signal,
            )
          : null,
        credentials.security
          ? request(
              'live',
              credentials,
              '/api/v1/security/session',
              sessionSchema,
              {},
              controller.signal,
            )
          : null,
      ])
      controller.signal.throwIfAborted()
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
  return (
    <SessionContext value={{ ...state, connect, cancelConnect, demo, disconnect }}>
      {children}
    </SessionContext>
  )
}
// Shared hooks are kept next to their provider; no state is persisted.
// eslint-disable-next-line react-refresh/only-export-components
export function useSession() {
  const value = useContext(SessionContext)
  if (!value) throw new Error('Session provider required')
  return value
}
