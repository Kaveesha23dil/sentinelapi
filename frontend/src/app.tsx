import { useEffect, useRef, useState, lazy, Suspense } from 'react'
import { Link, NavLink, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import {
  Activity,
  ArrowUpRight,
  Bell,
  Boxes,
  BrainCircuit,
  ChevronDown,
  ChevronRight,
  Clock3,
  LayoutDashboard,
  LogOut,
  Menu,
  Radio,
  RefreshCw,
  Shield,
  ShieldAlert,
  SlidersHorizontal,
  Unplug,
  X,
} from 'lucide-react'
import { useSession } from '@/hooks/session'
import { usePeriod } from '@/hooks/period'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Pill } from '@/components/common'
import { config, errorMessage } from '@/api/client'
const Overview = lazy(() => import('@/pages/overview').then((m) => ({ default: m.Overview })))
const Traffic = lazy(() => import('@/pages/traffic').then((m) => ({ default: m.Traffic })))
const Alerts = lazy(() => import('@/pages/security').then((m) => ({ default: m.Alerts })))
const Incident = lazy(() => import('@/pages/security').then((m) => ({ default: m.Incident })))
const Rules = lazy(() => import('@/pages/intelligence').then((m) => ({ default: m.Rules })))
const ML = lazy(() => import('@/pages/intelligence').then((m) => ({ default: m.ML })))
const Services = lazy(() => import('@/pages/services').then((m) => ({ default: m.Services })))

const navigation = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/traffic', label: 'API traffic', icon: Activity },
  { to: '/alerts', label: 'Threat alerts', icon: ShieldAlert },
  { to: '/rules', label: 'Detection rules', icon: SlidersHorizontal },
  { to: '/ml', label: 'ML monitoring', icon: BrainCircuit },
  { to: '/services', label: 'API services', icon: Boxes },
]
const descriptions: Record<string, string> = {
  '/': 'Your API perimeter, in perspective.',
  '/traffic': 'Explore sanitized requests across your API services.',
  '/alerts': 'Prioritize signals. Investigate with evidence.',
  '/rules': 'Explicit detection policies, transparent thresholds.',
  '/ml': 'Unusual behavior, measured with context.',
  '/services': 'Understand your monitored service landscape.',
}
function Connection({ open, onClose }: { open: boolean; onClose: () => void }) {
  const session = useSession()
  const { cancelConnect } = session
  const attempt = useRef(0)
  const ref = useRef<HTMLDialogElement>(null)
  const [monitoring, setMonitoring] = useState('')
  const [security, setSecurity] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  useEffect(() => {
    if (open) ref.current?.showModal()
    else {
      ref.current?.close()
    }
  }, [open])
  useEffect(() => {
    return () => {
      attempt.current += 1
      cancelConnect()
    }
  }, [open, cancelConnect])
  return (
    <dialog
      ref={ref}
      className="connection-dialog"
      aria-labelledby="connect-title"
      onCancel={onClose}
      onClose={() => {
        setMonitoring('')
        setSecurity('')
        setError('')
        setBusy(false)
        onClose()
      }}
    >
      <div className="dialog-head">
        <span className="logo-symbol">
          <Shield size={22} />
        </span>
        <Button
          size="icon"
          variant="ghost"
          aria-label="Close connection settings"
          onClick={onClose}
        >
          <X size={18} />
        </Button>
      </div>
      <h2 id="connect-title">Connect your workspace</h2>
      <p className="secondary">
        Use the existing SentinelAPI service credentials. Access is verified by the backend.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          if (!monitoring && !security) {
            setError('Enter at least one service credential.')
            return
          }
          setBusy(true)
          setError('')
          const currentAttempt = ++attempt.current
          void session
            .connect({ monitoring, security })
            .then(() => {
              if (currentAttempt !== attempt.current) return
              setMonitoring('')
              setSecurity('')
              onClose()
            })
            .catch((e) => {
              if (currentAttempt === attempt.current) setError(errorMessage(e))
            })
            .finally(() => {
              if (currentAttempt === attempt.current) setBusy(false)
            })
        }}
      >
        <label className="stack-label">
          Monitoring credential
          <Input
            type="password"
            autoComplete="off"
            value={monitoring}
            onChange={(e) => setMonitoring(e.target.value)}
            placeholder="Optional · traffic and API inventory"
          />
        </label>
        <label className="stack-label">
          Security credential
          <Input
            type="password"
            autoComplete="off"
            value={security}
            onChange={(e) => setSecurity(e.target.value)}
            placeholder="Optional · alerts, rules and ML"
          />
        </label>
        <div className="notice subtle small">
          <Shield size={16} />
          Credentials stay in memory and are cleared on disconnect or reload. Never paste them into
          screenshots.
        </div>
        {error && (
          <p className="error-text" role="alert">
            {error}
          </p>
        )}
        <Button className="w-full" type="submit" disabled={busy}>
          {busy ? 'Verifying access…' : 'Verify and connect'}
          <ArrowUpRight size={16} />
        </Button>
      </form>
    </dialog>
  )
}
function Layout() {
  const location = useLocation()
  const session = useSession()
  const period = usePeriod()
  const client = useQueryClient()
  const [connection, setConnection] = useState(false)
  const [menu, setMenu] = useState(false)
  const isIncident = location.pathname.startsWith('/alerts/')
  const title = isIncident
    ? 'Incident details'
    : (navigation.find((n) => n.to === location.pathname)?.label ?? 'Page not found')
  const refresh = () => {
    period.refresh()
    void client.invalidateQueries({ queryKey: ['api', session.epoch] })
  }
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <aside className={`sidebar ${menu ? 'mobile-open' : ''}`}>
        <Link to="/" className="brand" aria-label="SentinelAPI home">
          <span className="logo-symbol">
            <Shield size={23} />
          </span>
          <span>
            Sentinel<span className="brand-api">API</span>
            <small>SECURITY OPERATIONS</small>
          </span>
        </Link>
        <div className="workspace-switch">
          <div className="workspace-avatar">S</div>
          <div>
            <strong>Sentinel workspace</strong>
            <small>Local environment</small>
          </div>
          <ChevronDown size={14} />
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              aria-label={label}
              title={label}
              end={to === '/'}
              onClick={() => setMenu(false)}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon size={19} />
              <span>{label}</span>
              {to === '/ml' && <span className="nav-tag">LAB</span>}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="pipeline-card">
            <span className="pipeline-icon">
              <Radio size={18} />
            </span>
            <strong>Collection is independent</strong>
            <p>Dashboard availability does not affect gateway requests.</p>
            <span className="small secondary">WSO2 → Collector → PostgreSQL</span>
          </div>
          <div className="sidebar-footer">
            <span className="tiny-shield">
              <Shield size={14} />
            </span>
            SentinelAPI<span>v0.1</span>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="breadcrumbs">
            <Button
              className="mobile-menu"
              size="icon"
              variant="ghost"
              aria-label="Toggle navigation"
              aria-expanded={menu}
              onClick={() => setMenu(!menu)}
            >
              <Menu size={20} />
            </Button>
            <span className="hide-mobile">Workspace</span>
            <ChevronRight size={14} className="hide-mobile" />
            <strong>{title}</strong>
          </div>
          <div className="topbar-actions">
            <Pill
              tone={session.mode === 'demo' ? 'warning' : session.connected ? 'blue' : 'neutral'}
            >
              {session.mode === 'demo'
                ? 'Demo workspace'
                : session.connected
                  ? 'Backend session'
                  : 'Disconnected'}
            </Pill>
            <Link className="icon-link" to="/alerts" aria-label="Open security alert queue">
              <Bell size={18} />
            </Link>
            <span className="topbar-divider" />
            <details className="user-menu">
              <summary aria-label="Session menu">
                <span className="avatar">{session.connected ? 'OP' : '—'}</span>
                <span className="hide-mobile">{session.role}</span>
                <ChevronDown size={13} />
              </summary>
              <div className="user-dropdown">
                <strong>Session access</strong>
                <span>{session.mode === 'demo' ? 'Fixture observer' : session.role}</span>
                <Button variant="ghost" onClick={() => setConnection(true)}>
                  <Unplug size={15} />
                  Connection settings
                </Button>
                {session.connected && (
                  <Button variant="ghost" onClick={session.disconnect}>
                    <LogOut size={15} />
                    Disconnect
                  </Button>
                )}
              </div>
            </details>
          </div>
        </header>
        <main id="main-content" tabIndex={-1}>
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                SECURITY OPERATIONS / {isIncident ? 'INVESTIGATION' : title.toUpperCase()}
              </div>
              <h1>{title === 'Overview' ? 'Security overview' : title}</h1>
              <p>
                {descriptions[isIncident ? '/alerts' : location.pathname] ??
                  'Review the available record and its source evidence.'}
              </p>
            </div>
            <div className="page-actions">
              <Button variant="outline" size="sm" onClick={refresh} aria-label="Refresh dashboard">
                <RefreshCw size={14} />
                <span className="hide-mobile">Refresh</span>
              </Button>
              <label className="range-select">
                <Clock3 size={14} />
                <span className="sr-only">Time range</span>
                <select value={period.hours} onChange={(e) => period.setHours(e.target.value)}>
                  <option value="1">Last hour</option>
                  <option value="6">Last 6 hours</option>
                  <option value="24">Last 24 hours</option>
                  <option value="168">Last 7 days</option>
                </select>
              </label>
            </div>
          </div>
          {session.mode === 'demo' ? (
            <div className="demo-banner" role="status">
              <span>
                <strong>DEMO DATA</strong>Illustrative fixtures · No live backend connection ·
                Changes disabled
              </span>
              <Button size="sm" variant="ghost" onClick={() => setConnection(true)}>
                Connect backend
                <ArrowUpRight size={14} />
              </Button>
            </div>
          ) : !session.connected ? (
            <div className="connection-banner">
              <span>
                <Unplug size={18} />
                <span>
                  <strong>Connect to your security data</strong>
                  <small>Live APIs are never replaced with demo data on failure.</small>
                </span>
              </span>
              <div>
                {config.allowDemo && (
                  <Button size="sm" variant="outline" onClick={session.demo}>
                    Explore demo
                  </Button>
                )}
                <Button size="sm" onClick={() => setConnection(true)}>
                  Connect backend
                  <ArrowUpRight size={14} />
                </Button>
              </div>
            </div>
          ) : (
            <div className="source-bar">
              <span>
                <span className="status-dot" />
                Backend mode · observed event data · coverage unverified
              </span>
              <span>Polls every 30s while visible · UTC</span>
            </div>
          )}
          <div
            className="page-content"
            key={location.pathname + location.search + period.hours + session.epoch}
          >
            <Outlet />
          </div>
          <footer className="workspace-footer">
            <span>
              <Shield size={13} />
              SentinelAPI · Evidence-led API security
            </span>
            <span>
              {session.mode === 'demo'
                ? 'Historical demo anchor: 23 Oct 2026, 12:00 UTC'
                : 'Selected time window uses UTC'}
              <span className="footer-dot">·</span>Private local workspace
            </span>
          </footer>
        </main>
      </div>
      <Connection open={connection} onClose={() => setConnection(false)} />
    </div>
  )
}
export function App() {
  return (
    <Suspense
      fallback={
        <div className="data-state" role="status" aria-label="Loading view">
          Loading workspace…
        </div>
      }
    >
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Overview />} />
          <Route path="traffic" element={<Traffic />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="alerts/:id" element={<Incident />} />
          <Route path="rules" element={<Rules />} />
          <Route path="ml" element={<ML />} />
          <Route path="services" element={<Services />} />
          <Route
            path="*"
            element={
              <div className="data-state">
                <h2>Page not found</h2>
                <Link to="/">Return to overview</Link>
              </div>
            }
          />
        </Route>
      </Routes>
    </Suspense>
  )
}
