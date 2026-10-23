import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowUpRight, FileText, History, ShieldAlert } from 'lucide-react'
import {
  alertsSchema,
  alertDetailSchema,
  alertSchema,
  servicesSchema,
  rulesSchema,
  relatedSchema,
  historySchema,
  type Alert,
  type Service,
  type Status,
  type Rule,
} from '@/api/contracts'
import { useResource, usePatch } from '@/hooks/data'
import { usePeriod } from '@/hooks/period'
import { useSession } from '@/hooks/session'
import { Panel, State, Pagination, Pill, SafeEndpoint } from '@/components/common'
import { time, number } from '@/lib/format'
import { Button } from '@/components/ui/button'
import { errorMessage } from '@/api/client'

export function AlertsTable({
  alerts,
  services,
  compact = false,
  rules = [],
}: {
  alerts: Alert[]
  services: Service[]
  compact?: boolean
  rules?: Rule[]
}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Security signal</th>
            <th>Severity</th>
            {!compact && <th>Affected API</th>}
            <th>Status</th>
            <th>Detected · UTC</th>
            <th>
              <span className="sr-only">Details</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {alerts.map((a) => (
            <tr key={a.id}>
              <td>
                <Link className="incident-link" to={'/alerts/' + a.id}>
                  <span className={`signal-icon signal-${a.severity}`}>
                    <ShieldAlert size={15} />
                  </span>
                  <div>
                    <strong>
                      {a.rule_id
                        ? (rules.find((r) => r.id === a.rule_id)?.name.replaceAll('_', ' ') ??
                          'Rule-based security signal')
                        : 'Unassigned detector signal'}
                    </strong>
                    <small>
                      {a.rule_id
                        ? 'Rule-based observation'
                        : 'See evidence for detector attribution'}
                    </small>
                  </div>
                </Link>
              </td>
              <td>
                <Pill tone={a.severity}>{a.severity}</Pill>
              </td>
              {!compact && (
                <td>
                  {services.find((s) => s.id === a.api_service_id)?.name ??
                    a.api_service_id.slice(0, 8)}
                </td>
              )}
              <td>
                <Pill
                  tone={
                    a.status === 'investigating'
                      ? 'blue'
                      : a.status === 'resolved'
                        ? 'success'
                        : 'neutral'
                  }
                >
                  {a.status}
                </Pill>
              </td>
              <td className="nowrap secondary">{time(a.first_detected_at)}</td>
              <td>
                <Link to={'/alerts/' + a.id} aria-label={`Open incident ${a.id.slice(-4)}`}>
                  <ArrowUpRight size={16} />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
export function Alerts() {
  const { params } = usePeriod()
  const [page, setPage] = useState(1)
  const [severity, setSeverity] = useState('')
  const [status, setStatus] = useState('')
  const [rule, setRule] = useState('')
  const [sort, setSort] = useState('newest')
  const alerts = useResource('/api/v1/security/alerts', alertsSchema, {
    ...params,
    page,
    page_size: 20,
    severity,
    status,
    rule_id: rule,
  })
  const services = useResource('/api/v1/monitoring/services', servicesSchema, {
    ...params,
    page_size: 100,
  })
  const rules = useResource('/api/v1/security/rules', rulesSchema, { page_size: 100 })
  const change = (setter: (v: string) => void) => (e: React.ChangeEvent<HTMLSelectElement>) => {
    setter(e.target.value)
    setPage(1)
  }
  const ranks = { critical: 4, high: 3, medium: 2, low: 1 }
  const rows = [...(alerts.data?.alerts ?? [])].sort((a, b) =>
    sort === 'severity'
      ? ranks[b.severity] - ranks[a.severity]
      : b.last_detected_at.localeCompare(a.last_detected_at),
  )
  return (
    <>
      <div className="notice subtle">
        <ShieldAlert size={17} />
        Signals identify observed behavior. Review evidence before classifying an incident.
      </div>
      <Panel
        title="Security alert queue"
        subtitle="Newest server results; severity sorting applies to the returned page"
      >
        <div className="filters">
          <label>
            Severity
            <select value={severity} onChange={change(setSeverity)}>
              <option value="">All severities</option>
              {['critical', 'high', 'medium', 'low'].map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <label>
            Status
            <select value={status} onChange={change(setStatus)}>
              <option value="">All statuses</option>
              {['open', 'investigating', 'resolved', 'dismissed'].map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <label>
            Detection rule
            <select value={rule} onChange={change(setRule)}>
              <option value="">All detectors</option>
              {rules.data?.rules.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name.replaceAll('_', ' ')}
                </option>
              ))}
            </select>
          </label>
          <label>
            Sort returned page
            <select value={sort} onChange={(e) => setSort(e.target.value)}>
              <option value="newest">Newest first</option>
              <option value="severity">Severity first</option>
            </select>
          </label>
        </div>
        <State query={alerts} empty={rows.length === 0}>
          <AlertsTable
            alerts={rows}
            services={services.data?.services ?? []}
            rules={rules.data?.rules ?? []}
          />
        </State>
        <Pagination page={page} total={alerts.data?.total} onChange={setPage} />
      </Panel>
    </>
  )
}
const transitions: Record<Status, Status[]> = {
  open: ['investigating', 'resolved', 'dismissed'],
  investigating: ['resolved', 'dismissed'],
  resolved: [],
  dismissed: [],
}
export function Incident() {
  const { id = '' } = useParams()
  const { params } = usePeriod()
  const session = useSession()
  const detail = useResource(`/api/v1/security/alerts/${id}`, alertDetailSchema)
  const related = useResource(`/api/v1/security/alerts/${id}/events`, relatedSchema)
  const history = useResource(`/api/v1/security/alerts/${id}/history`, historySchema)
  const rules = useResource('/api/v1/security/rules', rulesSchema, { page_size: 100 })
  const services = useResource('/api/v1/monitoring/services', servicesSchema, {
    ...params,
    page_size: 100,
  })
  const patch = usePatch(`/api/v1/security/alerts/${id}`, alertSchema)
  const [target, setTarget] = useState('')
  const [confirm, setConfirm] = useState(false)
  const a = detail.data
  const permitted = session.mode === 'live' && session.capabilities.includes('alerts:update')
  return (
    <>
      <Link className="back-link" to="/alerts">
        <ArrowLeft size={15} />
        Back to alert queue
      </Link>
      <State query={detail}>
        <div className="incident-heading">
          <div className="incident-symbol">
            <ShieldAlert size={28} />
          </div>
          <div>
            <div className="eyebrow">INCIDENT · {id.slice(-8)}</div>
            <h2>{a?.title ?? 'Security signal'}</h2>
            <p>
              {services.data?.services.find((s) => s.id === a?.api_service_id)?.name ??
                'API reference: ' + a?.api_service_id}
            </p>
          </div>
          {a && <Pill tone={a.severity}>{a.severity} severity</Pill>}
        </div>
        <div className="detail-grid">
          <div>
            <Panel
              title="Detection evidence"
              subtitle="Server-recorded measurements and explanation"
              action={<FileText size={17} />}
            >
              <div className="detail-body">
                <div className="notice subtle">{a?.explanation}</div>
                <dl className="facts">
                  <div>
                    <dt>Detection rule</dt>
                    <dd>
                      {rules.data?.rules
                        .find((r) => r.id === a?.rule_id)
                        ?.name.replaceAll('_', ' ') ?? 'No rule assigned; review detector evidence'}
                    </dd>
                  </div>
                  <div>
                    <dt>Rule version</dt>
                    <dd>{number(a?.rule_version)}</dd>
                  </div>
                  <div>
                    <dt>Window start</dt>
                    <dd>{time(a?.window_start)}</dd>
                  </div>
                  <div>
                    <dt>Window end</dt>
                    <dd>{time(a?.window_end)}</dd>
                  </div>
                  <div>
                    <dt>Measured value</dt>
                    <dd>{number(a?.measured_value)}</dd>
                  </div>
                  <div>
                    <dt>Threshold</dt>
                    <dd>{number(a?.threshold)}</dd>
                  </div>
                </dl>
                <p className="small secondary">
                  {a?.risk_score_basis}. Measured units depend on the detector; raw decision scores
                  are not probabilities.
                </p>
                <h3 className="subheading">Evidence references</h3>
                <div className="evidence-list">
                  {a?.evidence.length === 0 ? (
                    <p>No linked evidence is available.</p>
                  ) : (
                    a?.evidence.map((e) => (
                      <div key={e.id}>
                        <span className="evidence-dot" />
                        <code>{e.event_id?.slice(0, 18) ?? 'Window summary'}</code>
                        <span>
                          {e.request_count === null
                            ? 'Count unavailable'
                            : `${e.request_count} requests`}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </Panel>
            <Panel title="Related API events" subtitle="Up to 100 sanitized event records">
              <State query={related} empty={related.data?.events.length === 0}>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Method / endpoint</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {related.data?.events.map((e) => (
                        <tr key={e.event_id}>
                          <td>{time(e.timestamp)}</td>
                          <td>
                            <span className="method">{e.http_method}</span>{' '}
                            <SafeEndpoint value={e.endpoint} />
                          </td>
                          <td>{e.status_code}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </State>
            </Panel>
          </div>
          <aside className="detail-sidebar">
            <Panel title="Investigation">
              <div className="detail-body">
                <div className="status-line">
                  <span>Current status</span>
                  {a && <Pill tone="blue">{a.status}</Pill>}
                </div>
                <p className="small secondary">First detected {time(a?.first_detected_at)}</p>
                {permitted && a && transitions[a.status].length > 0 ? (
                  <>
                    <label className="stack-label">
                      Update status
                      <select
                        value={target}
                        onChange={(e) => {
                          setTarget(e.target.value)
                          setConfirm(false)
                        }}
                      >
                        <option value="">Select a transition</option>
                        {transitions[a.status].map((s) => (
                          <option key={s}>{s}</option>
                        ))}
                      </select>
                    </label>
                    {confirm ? (
                      <div className="confirm-box">
                        <p>
                          Change this server-backed incident to <strong>{target}</strong>?
                        </p>
                        <Button
                          disabled={patch.isPending}
                          onClick={() =>
                            patch.mutate(
                              { status: target },
                              {
                                onSuccess: () => {
                                  setTarget('')
                                  setConfirm(false)
                                },
                              },
                            )
                          }
                        >
                          Confirm update
                        </Button>
                        <Button variant="ghost" onClick={() => setConfirm(false)}>
                          Cancel
                        </Button>
                      </div>
                    ) : (
                      <Button
                        className="w-full"
                        disabled={!target}
                        onClick={() => setConfirm(true)}
                      >
                        Review status change
                      </Button>
                    )}
                    {patch.isError && (
                      <p role="alert" className="error-text">
                        {errorMessage(patch.error)}
                      </p>
                    )}
                    {patch.isSuccess && <p role="status">Status saved on server.</p>}
                  </>
                ) : (
                  <p className="readonly-note">
                    {session.mode === 'demo'
                      ? 'Demo fixtures are read-only.'
                      : permitted
                        ? 'This incident has a terminal status.'
                        : 'Your session has read-only access.'}
                  </p>
                )}
              </div>
            </Panel>
            <Panel
              title="Audit history"
              subtitle="Recorded status transitions"
              action={<History size={17} />}
            >
              <State
                query={history}
                empty={history.data?.history.length === 0}
                emptyText="No recorded status transitions."
              >
                <div className="timeline">
                  {history.data?.history.map((h) => (
                    <div key={h.id}>
                      <span className="timeline-dot" />
                      <strong>
                        {h.from} → {h.to}
                      </strong>
                      <span>{time(h.timestamp)}</span>
                    </div>
                  ))}
                </div>
              </State>
            </Panel>
          </aside>
        </div>
      </State>
    </>
  )
}
