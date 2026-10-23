import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect } from 'react'
import { vi, it, expect } from 'vitest'
import { App } from '@/app'
import { SessionProvider, useSession } from '@/hooks/session'
import { PeriodProvider } from '@/hooks/period'
import { State, SafeEndpoint } from '@/components/common'
import { number, percent } from '@/lib/format'

vi.mock('@/components/charts', () => ({
  TrafficChart: () => <div>Traffic visualization</div>,
  StatusChart: () => <div>Status visualization</div>,
  ComparisonChart: () => <div>Comparison visualization</div>,
  ScoreChart: () => <div>Score visualization</div>,
}))
function Demo() {
  const { demo } = useSession()
  useEffect(() => demo(), [demo])
  return null
}
function view(path = '/', demo = false) {
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <MemoryRouter initialEntries={[path]}>
        <SessionProvider>
          <PeriodProvider>
            {demo && <Demo />}
            <App />
          </PeriodProvider>
        </SessionProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}
it('starts disconnected without silently loading fixtures', async () => {
  view()
  expect(await screen.findByText('Connect to your security data')).toBeInTheDocument()
  expect(screen.queryByText('DEMO DATA')).not.toBeInTheDocument()
})
it('navigates from explicit demo overview to API traffic', async () => {
  const user = userEvent.setup()
  view()
  await user.click(await screen.findByRole('button', { name: 'Explore demo' }))
  expect(await screen.findByText('DEMO DATA')).toBeInTheDocument()
  await user.click(screen.getByRole('link', { name: 'API traffic' }))
  expect(await screen.findByText('Gateway request log')).toBeInTheDocument()
  expect(await screen.findByText('Event reference')).toBeInTheDocument()
})
it('renders alert detail with read-only fixture evidence', async () => {
  view('/alerts/00000000-0000-4000-8000-000000000200', true)
  expect(await screen.findByText('Elevated API error ratio')).toBeInTheDocument()
  expect(screen.getByText('Measured value')).toBeInTheDocument()
  expect(screen.getByText('Demo fixtures are read-only.')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Review status change' })).not.toBeInTheDocument()
})
it('labels ML provenance and production limitations', async () => {
  view('/ml', true)
  expect(await screen.findByText('Production readiness pending')).toBeInTheDocument()
  expect(
    screen.getByText(/Synthetic evaluation is not live production performance/),
  ).toBeInTheDocument()
  expect(await screen.findAllByText('synthetic-controlled')).not.toHaveLength(0)
})
it('filters traffic and changes pages', async () => {
  const user = userEvent.setup()
  view('/traffic', true)
  await screen.findAllByText('86 records')
  await user.click(screen.getByRole('button', { name: 'Next page' }))
  await screen.findByText(/Page 2 of 5/)
  await user.selectOptions(screen.getByLabelText('HTTP method'), 'POST')
  await waitFor(() => expect(screen.getByText(/Page 1 of 1/)).toBeInTheDocument())
  expect(screen.getByRole('button', { name: 'Next page' })).toBeDisabled()
})
it('exposes accessible navigation and skip link', () => {
  view()
  expect(screen.getByRole('navigation', { name: 'Main navigation' })).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Skip to main content' })).toHaveAttribute(
    'href',
    '#main-content',
  )
  expect(screen.getByRole('link', { name: 'Overview' })).toHaveAttribute('aria-current', 'page')
})
it('represents unavailable ratios honestly and withholds unsafe endpoints', () => {
  expect(number(undefined)).toBe('Unavailable')
  expect(percent(null)).toBe('Unavailable')
  render(<SafeEndpoint value="/orders?token=private" />)
  expect(screen.getByText('[endpoint withheld]')).toBeInTheDocument()
})
it('renders loading and unauthorized error states', () => {
  const client = new QueryClient()
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}>
      <SessionProvider>{children}</SessionProvider>
    </QueryClientProvider>
  )
  const refetch = vi.fn()
  const { rerender } = render(
    <State
      query={{ isPending: true, isError: false, error: null, fetchStatus: 'fetching', refetch }}
    >
      Child
    </State>,
    { wrapper },
  )
  expect(screen.getByRole('status', { name: 'Loading data' })).toBeInTheDocument()
  rerender(
    <State
      query={{
        isPending: false,
        isError: true,
        error: new Error('network'),
        fetchStatus: 'idle',
        refetch,
      }}
    >
      Child
    </State>,
  )
  expect(screen.getByRole('alert')).toHaveTextContent('Unable to reach the API')
})
