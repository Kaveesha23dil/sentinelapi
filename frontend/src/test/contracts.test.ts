import { describe, it, expect } from 'vitest'
import {
  alertDetailSchema,
  alertsSchema,
  anomaliesSchema,
  endpointsSchema,
  evaluationSchema,
  eventsSchema,
  modelSchema,
  overviewSchema,
  relatedSchema,
  historySchema,
  rulesSchema,
  servicesSchema,
  seriesSchema,
} from '@/api/contracts'
import { fixtureResponse, DEMO_NOW } from '@/api/fixtures'
const params = { start: '2026-10-22T12:00:00.000Z', end: DEMO_NOW }
describe('Actual API contracts and explicit fixtures', () => {
  it.each([
    ['/monitoring/overview', overviewSchema],
    ['/monitoring/events', eventsSchema],
    ['/monitoring/services', servicesSchema],
    ['/monitoring/timeseries', seriesSchema],
    ['/monitoring/endpoints', endpointsSchema],
    ['/security/alerts', alertsSchema],
    ['/security/rules', rulesSchema],
    ['/ml/model', modelSchema],
    ['/ml/evaluation', evaluationSchema],
    ['/ml/anomalies', anomaliesSchema],
    ['/security/alerts/00000000-0000-4000-8000-000000000200', alertDetailSchema],
    ['/security/alerts/00000000-0000-4000-8000-000000000200/events', relatedSchema],
    ['/security/alerts/00000000-0000-4000-8000-000000000200/history', historySchema],
  ] as const)('validates %s', (suffix, schema) => {
    expect(schema.safeParse(fixtureResponse('/api/v1' + suffix, params)).success).toBe(true)
  })
  it('rejects invented/incompatible response fields', () => {
    expect(eventsSchema.safeParse({ items: [], count: 0 }).success).toBe(false)
    expect(modelSchema.safeParse({ state: 'running', accuracy: 99 }).success).toBe(false)
  })
  it('strips client identities from validated events', () => {
    const data = eventsSchema.parse(fixtureResponse('/api/v1/monitoring/events', params))
    expect(data.events[0]).not.toHaveProperty('client_identifier')
  })
  it('filters before pagination', () => {
    const data = eventsSchema.parse(
      fixtureResponse('/api/v1/monitoring/events', {
        ...params,
        http_method: 'POST',
        page_size: 2,
        page: 2,
      }),
    )
    expect(data.events).toHaveLength(2)
    expect(data.events.every((e) => e.http_method === 'POST')).toBe(true)
    expect(data.total).toBeGreaterThan(2)
  })
  it('returns empty data for an unobserved period', () => {
    const data = eventsSchema.parse(
      fixtureResponse('/api/v1/monitoring/events', {
        start: '2030-01-01T00:00:00.000Z',
        end: '2030-01-02T00:00:00.000Z',
      }),
    )
    expect(data.total).toBe(0)
  })
})
