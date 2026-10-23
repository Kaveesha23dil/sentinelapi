import {
  Activity,
  ArrowUpRight,
  Boxes,
  CircleAlert,
  Database,
  ShieldAlert,
  ShieldCheck,
  Zap,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useResource } from '@/hooks/data'
import { usePeriod } from '@/hooks/period'
import {
  overviewSchema,
  seriesSchema,
  endpointsSchema,
  servicesSchema,
  alertsSchema,
  summarySchema,
} from '@/api/contracts'
import { Panel, Metric, State, Pill, SafeEndpoint, TextLink } from '@/components/common'
import { number, percent, time } from '@/lib/format'
import { TrafficChart, StatusChart } from '@/components/charts'
import { AlertsTable } from './security'

export function Overview() {
  const { params, hours } = usePeriod()
  const overview = useResource('/api/v1/monitoring/overview', overviewSchema, params)
  const series = useResource('/api/v1/monitoring/timeseries', seriesSchema, params)
  const endpoints = useResource('/api/v1/monitoring/endpoints', endpointsSchema, params)
  const services = useResource('/api/v1/monitoring/services', servicesSchema, {
    ...params,
    page_size: 100,
  })
  const alerts = useResource('/api/v1/security/alerts', alertsSchema, { ...params, page_size: 5 })
  const summary = useResource('/api/v1/security/summary', summarySchema, params)
  const data = overview.data
  const hasRequests = !!data?.request_count
  const active = summary.data?.groups
    .filter((g) => ['open', 'investigating'].includes(g.status))
    .reduce((sum, g) => sum + g.count, 0)
  return (
    <>
      <div className="overview-note">
        <div className="note-symbol">
          <ShieldCheck size={20} />
        </div>
        <div>
          <strong>A clear view of your API perimeter</strong>
          <p>Observe traffic, investigate signals, and keep model evidence in context.</p>
        </div>
        <span className="hide-mobile">
          <Pill tone="blue">Evidence first</Pill>
        </span>
      </div>
      {(overview.isError || summary.isError || services.isError) && (
        <div className="notice warning">
          <CircleAlert size={16} />
          Partial data: one or more sources could not be loaded. Unavailable metrics are not zero.
        </div>
      )}
      <div className="metrics-grid">
        <Metric
          label="Total requests"
          value={number(data?.request_count)}
          note="Recorded in selected interval"
          icon={<Activity size={17} />}
        />
        <Metric
          label="Requests / minute"
          value={hasRequests ? number(data.request_count / (Number(hours) * 60)) : 'Unavailable'}
          note="Interval average, not peak rate"
          icon={<Zap size={17} />}
        />
        <Metric
          label="4xx error rate"
          value={hasRequests ? percent(data.error_4xx_count / data.request_count) : 'Unavailable'}
          note="Observed client error responses"
          icon={<CircleAlert size={17} />}
        />
        <Metric
          label="5xx error rate"
          value={hasRequests ? percent(data.error_5xx_count / data.request_count) : 'Unavailable'}
          note="Observed server error responses"
          icon={<Database size={17} />}
        />
        <Metric
          label="Active signals"
          value={number(active)}
          note="Open + investigating in interval"
          icon={<ShieldAlert size={17} />}
        />
        <Metric
          label="Registered APIs"
          value={number(services.data?.total)}
          note="Registered, not proof of full coverage"
          icon={<Boxes size={17} />}
        />
      </div>
      <div className="overview-charts">
        <Panel
          title="Request traffic"
          subtitle="Observed request counts per time bucket · UTC"
          action={
            <span className="chart-key">
              <i />
              Gateway traffic
            </span>
          }
        >
          <State query={series} empty={series.data?.points.length === 0}>
            {series.data && <TrafficChart points={series.data.points} />}
          </State>
          <div className="chart-foot">
            <span>Gaps indicate unobserved buckets; completeness is unverified.</span>
            <Pill>Event time</Pill>
          </div>
        </Panel>
        <Panel title="HTTP status distribution" subtitle="Responses recorded in this interval">
          <State query={overview} empty={data?.request_count === 0}>
            {data && <StatusChart breakdown={data.status_breakdown} />}
          </State>
        </Panel>
      </div>
      <div className="overview-bottom">
        <Panel
          title="Latest security alerts"
          subtitle="Observed signals requiring context and review"
          action={
            <Link to="/alerts">
              <TextLink>View all</TextLink>
            </Link>
          }
        >
          <State query={alerts} empty={alerts.data?.alerts.length === 0}>
            {alerts.data && (
              <AlertsTable
                alerts={alerts.data.alerts}
                services={services.data?.services ?? []}
                compact
              />
            )}
          </State>
        </Panel>
        <Panel
          title="Top endpoints"
          subtitle="Sanitized route templates"
          action={
            <Link to="/traffic" aria-label="View API traffic">
              <ArrowUpRight size={18} />
            </Link>
          }
        >
          <State query={endpoints} empty={endpoints.data?.endpoints.length === 0}>
            <div className="endpoint-list">
              {endpoints.data?.endpoints.map((e, i) => (
                <div key={e.http_method + e.endpoint}>
                  <span className="rank">0{i + 1}</span>
                  <div>
                    <SafeEndpoint value={e.endpoint} />
                    <small>{e.http_method}</small>
                  </div>
                  <strong>{number(e.request_count)}</strong>
                </div>
              ))}
            </div>
          </State>
        </Panel>
      </div>
      <div className="bottom-note">
        <ShieldCheck size={15} />
        <span>An alert is an investigation signal, not proof of malicious activity.</span>
        <span className="last-range">Window ends {time(params.end)}</span>
      </div>
    </>
  )
}
