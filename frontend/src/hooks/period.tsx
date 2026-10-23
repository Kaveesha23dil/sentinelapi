import { createContext, useContext, useMemo, useState, useEffect, type ReactNode } from 'react'
import { useSession } from './session'
import { DEMO_NOW } from '@/api/demo-clock'
type Period = {
  hours: string
  setHours: (value: string) => void
  params: { start: string; end: string }
  refresh: () => void
  historical: boolean
}
const Context = createContext<Period | null>(null)
export function PeriodProvider({ children }: { children: ReactNode }) {
  const { mode, connected } = useSession()
  const [hours, setHours] = useState('24')
  const [anchor, setAnchor] = useState(() => Date.now())
  useEffect(() => {
    if (mode !== 'live' || !connected) return
    const timer = setInterval(() => {
      if (document.visibilityState === 'visible') setAnchor(Date.now())
    }, 30000)
    return () => clearInterval(timer)
  }, [mode, connected])
  const end = mode === 'demo' ? Date.parse(DEMO_NOW) : anchor
  const params = useMemo(
    () => ({
      start: new Date(end - Number(hours) * 3600000).toISOString(),
      end: new Date(end).toISOString(),
    }),
    [end, hours],
  )
  return (
    <Context
      value={{
        hours,
        setHours,
        params,
        refresh: () => setAnchor(Date.now()),
        historical: mode === 'demo',
      }}
    >
      {children}
    </Context>
  )
}
// eslint-disable-next-line react-refresh/only-export-components
export function usePeriod() {
  const value = useContext(Context)
  if (!value) throw new Error('Period provider required')
  return value
}
