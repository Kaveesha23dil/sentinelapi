import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Filter } from 'lucide-react'
import { eventsSchema, servicesSchema } from '@/api/contracts'
import { useResource } from '@/hooks/data'
import { usePeriod } from '@/hooks/period'
import { Panel, State, Pagination, Pill, SafeEndpoint } from '@/components/common'
import { time, number } from '@/lib/format'

export function Traffic() {
  const { params } = usePeriod()
  const [search] = useSearchParams()
  const [page, setPage] = useState(1)
  const [api, setApi] = useState(search.get('api_id') ?? '')
  const [method, setMethod] = useState('')
  const [status, setStatus] = useState('')
  const services = useResource('/api/v1/monitoring/services', servicesSchema, {
    ...params,
    page_size: 100,
  })
  const events = useResource('/api/v1/monitoring/events', eventsSchema, {
    ...params,
    page,
    page_size: 20,
    api_id: api,
    http_method: method,
    status_code: status,
  })
  const change = (setter: (v: string) => void) => (e: React.ChangeEvent<HTMLSelectElement>) => {
    setter(e.target.value)
    setPage(1)
  }
  return (
    <Panel
      title="Gateway request log"
      subtitle="Sanitized completed-response events · newest first"
      action={<Pill tone="blue">{number(events.data?.total)} records</Pill>}
    >
      <div className="filters">
        <Filter size={16} />
        <label>
          API service
          <select value={api} onChange={change(setApi)}>
            <option value="">All APIs</option>
            {services.data?.services.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          HTTP method
          <select value={method} onChange={change(setMethod)}>
            <option value="">All methods</option>
            {['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'].map((m) => (
              <option key={m}>{m}</option>
            ))}
          </select>
        </label>
        <label>
          HTTP status
          <select value={status} onChange={change(setStatus)}>
            <option value="">All statuses</option>
            {[200, 201, 204, 400, 401, 403, 404, 429, 500, 502, 503].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
      </div>
      <State query={events} empty={events.data?.events.length === 0}>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Timestamp · UTC</th>
                <th>Method</th>
                <th>Endpoint</th>
                <th>Status</th>
                <th>API</th>
                <th>Event reference</th>
              </tr>
            </thead>
            <tbody>
              {events.data?.events.map((e) => (
                <tr key={e.event_id}>
                  <td className="nowrap">{time(e.timestamp)}</td>
                  <td>
                    <span className={`method method-${e.http_method.toLowerCase()}`}>
                      {e.http_method}
                    </span>
                  </td>
                  <td>
                    <SafeEndpoint value={e.endpoint} />
                  </td>
                  <td>
                    <Pill
                      tone={
                        e.status_code >= 500
                          ? 'critical'
                          : e.status_code >= 400
                            ? 'warning'
                            : 'success'
                      }
                    >
                      {e.status_code}
                    </Pill>
                  </td>
                  <td>
                    {services.data?.services.find((s) => s.id === e.api_service_id)?.name ??
                      e.api_service_id.slice(0, 8)}
                  </td>
                  <td>
                    <code title={e.event_id}>{e.event_id.slice(0, 8)}…</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </State>
      <Pagination page={page} onChange={setPage} total={events.data?.total} />
      <div className="panel-foot">
        Event references are collector deduplication IDs. Gateway correlation IDs and client
        identities are not exposed.
      </div>
    </Panel>
  )
}
