import { useState } from 'react'
import { Boxes, ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'
import { servicesSchema } from '@/api/contracts'
import { useResource } from '@/hooks/data'
import { usePeriod } from '@/hooks/period'
import { Panel, State, Pagination, Pill, SafeEndpoint } from '@/components/common'
import { time, number } from '@/lib/format'
export function Services() {
  const { params } = usePeriod()
  const [page, setPage] = useState(1)
  const services = useResource('/api/v1/monitoring/services', servicesSchema, {
    ...params,
    page,
    page_size: 12,
  })
  return (
    <>
      <div className="notice subtle">
        <Boxes size={18} />
        API registration and observed traffic do not establish endpoint health or complete gateway
        coverage.
      </div>
      <Panel
        title="API service inventory"
        subtitle="Registered services and event coverage for the selected interval"
        action={<Pill tone="blue">{number(services.data?.total)} registered</Pill>}
      >
        <State query={services} empty={services.data?.services.length === 0}>
          <div className="services-grid">
            {services.data?.services.map((s) => (
              <article className="service-card" key={s.id}>
                <div className="service-top">
                  <span className="service-icon">
                    <Boxes size={22} />
                  </span>
                  <Pill tone={s.request_count > 0 ? 'blue' : 'neutral'}>
                    {s.request_count > 0 ? 'Traffic observed' : 'No traffic observed'}
                  </Pill>
                </div>
                <h3>{s.name}</h3>
                <span className="service-version">VERSION {s.version}</span>
                <div className="context-label">
                  Gateway context
                  <SafeEndpoint value={s.context} />
                </div>
                <div className="service-stats">
                  <div>
                    <span>Recorded requests</span>
                    <strong>{number(s.request_count)}</strong>
                  </div>
                  <div>
                    <span>Service health</span>
                    <strong>{s.health ?? 'Unavailable'}</strong>
                  </div>
                </div>
                <div className="coverage-line">
                  <span>Last observed</span>
                  <span>{time(s.last_event)}</span>
                </div>
                <p className="small secondary">
                  Coverage: {s.coverage.replaceAll('-', ' ')}. No heartbeat measurement available.
                </p>
                <Link className="text-link" to={'/traffic?api_id=' + s.id}>
                  Inspect API traffic
                  <ExternalLink size={14} />
                </Link>
              </article>
            ))}
          </div>
        </State>
        <Pagination page={page} size={12} total={services.data?.total} onChange={setPage} />
      </Panel>
    </>
  )
}
