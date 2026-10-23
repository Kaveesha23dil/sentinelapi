// Explicit illustrative fixtures. Never a fallback for failed live requests.
import type { Params } from './client'
import evaluation from './synthetic-evaluation.json' with { type: 'json' }
import { DEMO_NOW } from './demo-clock'

export { DEMO_NOW } from './demo-clock'
const uuid = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, '0')}`
const services = [
  {
    id: uuid(1),
    name: 'DemoCommerce API',
    version: '1.0.0',
    context: '/democommerceapi',
    request_count: 1248,
  },
  {
    id: uuid(2),
    name: 'Payments sandbox',
    version: '2.1.0',
    context: '/demo/payments',
    request_count: 632,
  },
  {
    id: uuid(3),
    name: 'Identity sandbox',
    version: '1.2.0',
    context: '/demo/identity',
    request_count: 416,
  },
].map((s) => ({
  ...s,
  first_event: '2026-10-23T00:00:00.000Z',
  last_event: '2026-10-23T11:59:42.000Z',
  health: null,
  coverage: 'demo-fixture',
}))
const kinds = ['error_rate', 'request_flood', 'enumeration', 'auth_failures', 'unusual_activity']
const rules = kinds.map((kind, i) => ({
  id: uuid(100 + i),
  name: kind,
  rule_type: kind,
  enabled: i === 0,
  live_supported: i === 0,
  configuration: {
    version: 1,
    window_seconds: [300, 60, 120, 120, 300][i],
    threshold: [0.5, 100, 15, 10, 3][i],
    minimum_requests: i === 0 ? 20 : 1,
    baseline_windows: 12,
  },
}))
const alerts = Array.from({ length: 8 }, (_, i) => ({
  id: uuid(200 + i),
  api_service_id: uuid((i % 3) + 1),
  rule_id: i === 2 ? null : uuid(100),
  rule_version: i === 2 ? null : 1,
  severity: ['high', 'medium', 'medium', 'low'][i % 4],
  status: ['open', 'investigating', 'open', 'resolved'][i % 4],
  risk_score: 50,
  first_detected_at: `2026-10-23T${String(11 - i).padStart(2, '0')}:24:00.000Z`,
  last_detected_at: `2026-10-23T${String(11 - i).padStart(2, '0')}:26:00.000Z`,
  window_start: `2026-10-23T${String(11 - i).padStart(2, '0')}:20:00.000Z`,
  window_end: `2026-10-23T${String(11 - i).padStart(2, '0')}:25:00.000Z`,
  measured_value: i === 2 ? -0.087 : 0.68,
  threshold: i === 2 ? 0 : 0.5,
  explanation:
    i === 2
      ? 'DEMO: an unusual 60-second traffic window. Anomalous behavior does not establish malicious intent.'
      : 'DEMO: the observed HTTP error ratio exceeded the configured threshold. Review the linked sanitized events before drawing conclusions.',
  risk_score_basis: 'Fixed medium-severity policy score; not a probability',
  origin: 'demo-fixture',
}))
const buckets = [2, 4, 3, 7, 6, 8, 4, 10, 6, 9, 5, 8, 6, 8]
function eventTime(index: number) {
  let before = 0
  for (let bucket = 0; bucket < buckets.length; bucket++) {
    if (index < before + buckets[bucket])
      return new Date(
        Date.parse(DEMO_NOW) - (bucket + 1) * 1800000 + (index - before) * 2000,
      ).toISOString()
    before += buckets[bucket]
  }
  return DEMO_NOW
}
const events = Array.from({ length: 86 }, (_, i) => ({
  event_id: uuid(1000 + i),
  api_service_id: uuid((i % 3) + 1),
  timestamp: eventTime(i),
  http_method: i % 5 === 0 ? 'POST' : 'GET',
  endpoint: [
    '/api/v1/products',
    '/api/v1/orders',
    '/api/v1/orders/{order_id}',
    '/api/v1/categories',
  ][i % 4],
  status_code: i % 11 === 0 ? 500 : i % 7 === 0 ? 404 : i % 5 === 0 ? 201 : 200,
  latency_ms: null,
  source: 'demo-fixture',
}))
const paginate = <T>(rows: T[], key: string, p: Params) => ({
  page: Number(p.page ?? 1),
  page_size: Number(p.page_size ?? 20),
  total: rows.length,
  [key]: rows.slice(
    (Number(p.page ?? 1) - 1) * Number(p.page_size ?? 20),
    Number(p.page ?? 1) * Number(p.page_size ?? 20),
  ),
})
const within = (time: string, p: Params) =>
  (!p.start || time >= p.start) && (!p.end || time < p.end)

export function fixtureResponse(path: string, p: Params): unknown {
  const selectedEvents = events.filter(
    (e) =>
      within(e.timestamp, p) &&
      (!p.api_id || e.api_service_id === p.api_id) &&
      (!p.http_method || e.http_method === p.http_method) &&
      (!p.status_code || e.status_code === Number(p.status_code)),
  )
  const selectedAlerts = alerts.filter(
    (a) =>
      within(a.last_detected_at, p) &&
      (!p.api_id || a.api_service_id === p.api_id) &&
      (!p.severity || a.severity === p.severity) &&
      (!p.status || a.status === p.status) &&
      (!p.rule_id || a.rule_id === p.rule_id),
  )
  if (path.endsWith('/session'))
    return {
      role: path.includes('/monitoring/') ? 'monitor' : 'reader',
      capabilities: [path.includes('/monitoring/') ? 'monitoring:read' : 'security:read'],
    }
  if (path.endsWith('/services'))
    return paginate(
      services.map((s) => {
        const rows = selectedEvents.filter((e) => e.api_service_id === s.id)
        return {
          ...s,
          request_count: rows.length,
          first_event: rows.at(-1)?.timestamp ?? null,
          last_event: rows[0]?.timestamp ?? null,
        }
      }),
      'services',
      p,
    )
  if (path.endsWith('/overview')) {
    const breakdown: Record<string, number> = {}
    selectedEvents.forEach((e) => {
      breakdown[e.status_code] = (breakdown[e.status_code] ?? 0) + 1
    })
    return {
      start: p.start,
      end: p.end,
      request_count: selectedEvents.length,
      error_4xx_count: selectedEvents.filter((e) => e.status_code >= 400 && e.status_code < 500)
        .length,
      error_5xx_count: selectedEvents.filter((e) => e.status_code >= 500).length,
      average_latency_ms: null,
      status_breakdown: breakdown,
    }
  }
  if (path.endsWith('/timeseries')) {
    const bins = new Map<string, number>()
    selectedEvents.forEach((e) => {
      const t = e.timestamp.slice(0, 16) + ':00.000Z'
      bins.set(t, (bins.get(t) ?? 0) + 1)
    })
    return {
      start: p.start,
      end: p.end,
      bucket_seconds: 60,
      points: [...bins].sort().map(([timestamp, requests]) => ({ timestamp, requests })),
      coverage: 'demo-fixture',
    }
  }
  if (path.endsWith('/endpoints')) {
    const bins = new Map<string, number>()
    selectedEvents.forEach((e) => {
      const key = e.http_method + ' ' + e.endpoint
      bins.set(key, (bins.get(key) ?? 0) + 1)
    })
    return {
      endpoints: [...bins]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([key, request_count]) => ({
          http_method: key.split(' ')[0],
          endpoint: key.split(' ')[1],
          request_count,
        })),
    }
  }
  if (path.endsWith('/events') && path.includes('/monitoring/'))
    return paginate(selectedEvents, 'events', p)
  if (path.endsWith('/alerts')) return paginate(selectedAlerts, 'alerts', p)
  if (path.endsWith('/rules')) return paginate(rules, 'rules', p)
  if (path.endsWith('/summary'))
    return {
      groups: ['open', 'investigating', 'resolved', 'dismissed'].flatMap((status) =>
        ['critical', 'high', 'medium', 'low'].map((severity) => ({
          status,
          severity,
          count: selectedAlerts.filter((a) => a.status === status && a.severity === severity)
            .length,
        })),
      ),
    }
  if (path.endsWith('/model'))
    return {
      state: 'experimental',
      production_ready: false,
      model_version: evaluation.model_version,
      provenance: 'synthetic-controlled',
      features: [
        'request_count',
        'error_4xx_ratio',
        'error_5xx_ratio',
        'unique_endpoints',
        'get_ratio',
        'post_ratio',
        'status_code_diversity',
      ],
      schema: 'api-60s-v1',
      trained_at: '2026-10-23T08:19:23.000Z',
      worker_status: 'demo-not-connected',
      deployment_enabled: false,
      score_calibration: null,
    }
  if (path.endsWith('/evaluation')) return evaluation
  if (path.endsWith('/anomalies'))
    return paginate(
      [-0.087, -0.046, -0.112, -0.023].map((decision_score, i) => ({
        window_id: `demo-window-${i}`,
        window_start: `2026-10-23T11:${20 + i}:00.000Z`,
        window_end: `2026-10-23T11:${21 + i}:00.000Z`,
        api_service_id: uuid(1),
        model_version: evaluation.model_version,
        schema_version: 'api-60s-v1',
        decision_score,
        features: { request_count: 136, error_4xx_ratio: 0.4, error_5xx_ratio: 0.2 },
        provenance: 'demo-fixture',
        alert_id: uuid(202),
      })),
      'anomalies',
      p,
    )
  const id = path.split('/')[5]
  const alert = alerts.find((a) => a.id === id)
  if (!alert) throw new Error('Fixture record not found')
  if (path.endsWith('/events'))
    return {
      events: events
        .slice(0, 5)
        .map(({ event_id, timestamp, http_method, endpoint, status_code }) => ({
          event_id,
          timestamp,
          http_method,
          endpoint,
          status_code,
        })),
      limit: 100,
    }
  if (path.endsWith('/history'))
    return {
      history:
        alert.status === 'investigating'
          ? [
              {
                id: uuid(500),
                timestamp: alert.last_detected_at,
                action: 'alert.status',
                from: 'open',
                to: 'investigating',
              },
            ]
          : [],
    }
  return {
    ...alert,
    title: alert.rule_id ? 'Elevated API error ratio' : 'Unusual API traffic window',
    evidence: events
      .slice(0, 5)
      .map((e, i) => ({ id: uuid(600 + i), event_id: e.event_id, request_count: 24 })),
  }
}
