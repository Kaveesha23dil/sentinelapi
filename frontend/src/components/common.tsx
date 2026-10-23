import { Component, type ReactNode } from 'react'
import {
  AlertCircle,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  Database,
  RotateCw,
} from 'lucide-react'
import type { UseQueryResult } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { errorMessage } from '@/api/client'
import { useSession } from '@/hooks/session'
import { cn } from '@/lib/utils'

export function Panel({
  title,
  subtitle,
  action,
  children,
  className,
}: {
  title: string
  subtitle?: string
  action?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <section className={cn('panel', className)}>
      <div className="panel-head">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  )
}
export function Pill({ children, tone = 'neutral' }: { children: ReactNode; tone?: string }) {
  return (
    <span className={`pill pill-${tone}`}>
      <span className="pill-dot" />
      {children}
    </span>
  )
}
export function State({
  query,
  children,
  empty = false,
  emptyText = 'No records in this interval.',
}: {
  query: Pick<UseQueryResult, 'isPending' | 'isError' | 'error' | 'refetch' | 'fetchStatus'>
  children: ReactNode
  empty?: boolean
  emptyText?: string
}) {
  const session = useSession()
  if (query.isPending && query.fetchStatus === 'idle')
    return (
      <div className="data-state">
        <Database />
        <p>
          {session.connected
            ? 'This session has no access to this data source.'
            : 'Connect a backend session or explore the labeled demo.'}
        </p>
      </div>
    )
  if (query.isPending)
    return (
      <div role="status" aria-label="Loading data" className="loading-stack">
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-8 w-full" />
      </div>
    )
  if (query.isError)
    return (
      <div role="alert" className="data-state error">
        <AlertCircle />
        <p>{errorMessage(query.error)}</p>
        <Button variant="outline" size="sm" onClick={() => void query.refetch()}>
          <RotateCw size={14} />
          Retry
        </Button>
      </div>
    )
  if (empty)
    return (
      <div className="data-state">
        <Database />
        <p>{emptyText}</p>
      </div>
    )
  return children
}
export function Pagination({
  page,
  total,
  size = 20,
  onChange,
}: {
  page: number
  total?: number
  size?: number
  onChange: (page: number) => void
}) {
  const pages = Math.max(1, Math.ceil((total ?? 0) / size))
  return (
    <div className="pagination">
      <span>
        {total === undefined ? 'Total unavailable' : `${total.toLocaleString()} records`}
        <span className="hide-mobile">
          {' '}
          · Page {page} of {pages}
        </span>
      </span>
      <div>
        <Button
          aria-label="Previous page"
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
        >
          <ChevronLeft size={16} />
        </Button>
        <Button
          aria-label="Next page"
          variant="outline"
          size="sm"
          disabled={total === undefined || page >= pages}
          onClick={() => onChange(page + 1)}
        >
          <ChevronRight size={16} />
        </Button>
      </div>
    </div>
  )
}
export function SafeEndpoint({ value }: { value: string }) {
  // Defense in depth: collector templates only; omit queries, URL hosts and IDs.
  const safe =
    value.startsWith('/') && !/[?&#@]|https?:|\b\d{1,3}(\.\d{1,3}){3}\b/i.test(value)
      ? value
      : '[endpoint withheld]'
  return (
    <code className="endpoint" title={safe}>
      {safe}
    </code>
  )
}
export function Metric({
  label,
  value,
  note,
  icon,
}: {
  label: string
  value: string
  note: string
  icon: ReactNode
}) {
  return (
    <div className="metric">
      <div className="metric-top">
        <span>{label}</span>
        <span className="metric-icon">{icon}</span>
      </div>
      <strong>{value}</strong>
      <span className="metric-note">{note}</span>
    </div>
  )
}
export function TextLink({ children }: { children: ReactNode }) {
  return (
    <span className="text-link">
      {children}
      <ArrowUpRight size={14} />
    </span>
  )
}
export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() {
    return { failed: true }
  }
  render() {
    return this.state.failed ? (
      <main className="fatal" role="alert">
        <h1>This view could not be displayed.</h1>
        <p>No changes were sent. Reload to recover your session.</p>
        <Button onClick={() => window.location.reload()}>Reload application</Button>
      </main>
    ) : (
      this.props.children
    )
  }
}
