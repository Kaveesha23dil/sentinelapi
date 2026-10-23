import { z } from 'zod'

const stamp = z.string().datetime({ offset: true })
const numeric = z.union([
  z.number(),
  z
    .string()
    .regex(/^-?\d+(\.\d+)?$/)
    .transform(Number),
])
const count = z.number().int().nonnegative()
export const sessionSchema = z.object({
  role: z.enum(['monitor', 'reader', 'analyst', 'admin']),
  capabilities: z.array(z.string()),
})
export const overviewSchema = z.object({
  start: stamp,
  end: stamp,
  request_count: count,
  error_4xx_count: count,
  error_5xx_count: count,
  average_latency_ms: z.number().nullable(),
  status_breakdown: z.record(z.string(), count),
})
export const eventSchema = z.object({
  event_id: z.string().uuid(),
  api_service_id: z.string().uuid(),
  timestamp: stamp,
  http_method: z.string(),
  endpoint: z.string(),
  status_code: z.number().int().min(100).max(599),
  latency_ms: numeric.nullable(),
  source: z.string(),
})
export const relatedEventSchema = eventSchema.omit({
  api_service_id: true,
  latency_ms: true,
  source: true,
})
const pagination = {
  page: z.number().int().positive(),
  page_size: z.number().int().positive(),
  total: count,
}
export const eventsSchema = z.object({ ...pagination, events: z.array(eventSchema) })
export const serviceSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  version: z.string(),
  context: z.string(),
  request_count: count,
  first_event: stamp.nullable(),
  last_event: stamp.nullable(),
  health: z.string().nullable(),
  coverage: z.string(),
})
export const servicesSchema = z.object({ ...pagination, services: z.array(serviceSchema) })
export const seriesSchema = z.object({
  start: stamp,
  end: stamp,
  bucket_seconds: count,
  points: z.array(z.object({ timestamp: stamp, requests: count })),
  coverage: z.string(),
})
export const endpointsSchema = z.object({
  endpoints: z.array(
    z.object({ endpoint: z.string(), http_method: z.string(), request_count: count }),
  ),
})
export const severitySchema = z.enum(['critical', 'high', 'medium', 'low'])
export const statusSchema = z.enum(['open', 'investigating', 'resolved', 'dismissed'])
export const alertSchema = z.object({
  id: z.string().uuid(),
  api_service_id: z.string().uuid(),
  rule_id: z.string().uuid().nullable(),
  rule_version: z.number().nullable(),
  severity: severitySchema,
  status: statusSchema,
  risk_score: numeric,
  first_detected_at: stamp,
  last_detected_at: stamp,
  window_start: stamp.nullable(),
  window_end: stamp.nullable(),
  measured_value: numeric.nullable(),
  threshold: numeric.nullable(),
  explanation: z.string(),
  risk_score_basis: z.string(),
  origin: z.string(),
})
export const alertsSchema = z.object({ ...pagination, alerts: z.array(alertSchema) })
export const alertDetailSchema = alertSchema.extend({
  title: z.string().optional(),
  evidence: z.array(
    z.object({
      id: z.string().uuid(),
      event_id: z.string().uuid().nullable(),
      request_count: z.number().nullable(),
    }),
  ),
})
export const relatedSchema = z.object({ events: z.array(relatedEventSchema), limit: count })
export const historySchema = z.object({
  history: z.array(
    z.object({
      id: z.string().uuid(),
      timestamp: stamp,
      action: z.string(),
      from: statusSchema.nullable(),
      to: statusSchema.nullable(),
    }),
  ),
})
export const ruleSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  rule_type: z.string(),
  configuration: z
    .object({
      version: z.number(),
      window_seconds: z.number(),
      threshold: z.number(),
      minimum_requests: z.number(),
      baseline_windows: z.number(),
    })
    .nullable(),
  enabled: z.boolean(),
  live_supported: z.boolean(),
})
export const rulesSchema = z.object({ ...pagination, rules: z.array(ruleSchema) })
export const summarySchema = z.object({
  groups: z.array(z.object({ status: statusSchema, severity: severitySchema, count })),
})
export const modelSchema = z.object({
  state: z.enum(['unavailable', 'experimental', 'ready']),
  production_ready: z.boolean(),
  model_version: z.string().optional(),
  provenance: z.string().optional(),
  features: z.array(z.string()).optional(),
  schema: z.string().optional(),
  trained_at: stamp.optional(),
  worker_status: z.string().optional(),
  deployment_enabled: z.boolean().optional(),
  score_calibration: z.null().optional(),
})
const metricsSchema = z.object({
  confusion_matrix: z.array(z.array(count)),
  precision: z.number().min(0).max(1).nullable(),
  recall: z.number().min(0).max(1).nullable(),
  f1: z.number().min(0).max(1).nullable(),
  false_positive_rate: z.number().min(0).max(1).nullable(),
  windows: count,
  class_distribution: z.object({ normal: count, controlled_scenario: count }),
})
export const evaluationSchema = z.object({
  provenance: z.string(),
  production_ready: z.boolean(),
  model_version: z.string(),
  evaluation_date: stamp,
  evaluation_windows: count,
  ml: metricsSchema,
  rules: metricsSchema,
  detection_latency_seconds: z.number().nullable(),
})
export const anomalySchema = z.object({
  window_id: z.string(),
  window_start: stamp,
  window_end: stamp,
  api_service_id: z.string().uuid(),
  model_version: z.string(),
  schema_version: z.string(),
  decision_score: z.number(),
  features: z.record(z.string(), z.number()),
  provenance: z.string(),
  alert_id: z.string().uuid().nullable(),
})
export const anomaliesSchema = z.object({ ...pagination, anomalies: z.array(anomalySchema) })
export type Alert = z.infer<typeof alertSchema>
export type Rule = z.infer<typeof ruleSchema>
export type Service = z.infer<typeof serviceSchema>
export type TrafficEvent = z.infer<typeof eventSchema>
export type Status = z.infer<typeof statusSchema>
export type Model = z.infer<typeof modelSchema>
export type Evaluation = z.infer<typeof evaluationSchema>
