import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BrainCircuit, CircleAlert, SlidersHorizontal } from 'lucide-react'
import {
  ruleSchema,
  rulesSchema,
  modelSchema,
  evaluationSchema,
  anomaliesSchema,
  type Rule,
} from '@/api/contracts'
import { useResource, usePatch } from '@/hooks/data'
import { usePeriod } from '@/hooks/period'
import { useSession } from '@/hooks/session'
import { Panel, State, Pagination, Pill } from '@/components/common'
import { number, percent, time } from '@/lib/format'
import { ComparisonChart, ScoreChart } from '@/components/charts'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { errorMessage } from '@/api/client'

const descriptions: Record<string, string> = {
  error_rate: 'Detects a high proportion of observed HTTP error responses.',
  request_flood: 'Request-volume strategy requiring verified pseudonymous client identity.',
  enumeration: 'Unknown-route strategy requiring trusted route and client evidence.',
  auth_failures: 'Authentication-failure strategy requiring confirmed authentication evidence.',
  unusual_activity: 'Baseline strategy requiring adequate trusted historical windows.',
}
function RuleCard({ rule }: { rule: Rule }) {
  const session = useSession()
  const [editing, setEditing] = useState(false)
  const [threshold, setThreshold] = useState(String(rule.configuration?.threshold ?? ''))
  const [seconds, setSeconds] = useState(String(rule.configuration?.window_seconds ?? ''))
  const [enabled, setEnabled] = useState(rule.enabled)
  const patch = usePatch('/api/v1/security/rules/' + rule.id, ruleSchema)
  const allowed =
    session.mode === 'live' &&
    session.capabilities.includes('rules:update') &&
    rule.configuration !== null
  const valid =
    Number.isFinite(Number(threshold)) &&
    Number(threshold) > 0 &&
    Number.isInteger(Number(seconds)) &&
    Number(seconds) >= 1 &&
    Number(seconds) <= 300 &&
    (rule.rule_type !== 'error_rate' || Number(threshold) <= 1)
  return (
    <div className="rule-card">
      <div className="rule-card-top">
        <span className="rule-icon">
          <SlidersHorizontal size={19} />
        </span>
        <Pill tone={rule.enabled ? 'success' : 'neutral'}>
          {rule.enabled ? 'Enabled' : 'Disabled'}
        </Pill>
      </div>
      <h3>{rule.name.replaceAll('_', ' ')}</h3>
      <p>
        {descriptions[rule.rule_type] ??
          'Unsupported legacy configuration; editing may be rejected.'}
      </p>
      <div className="rule-values">
        <div>
          <span>Threshold</span>
          <strong>{number(rule.configuration?.threshold)}</strong>
        </div>
        <div>
          <span>Window</span>
          <strong>
            {rule.configuration ? `${rule.configuration.window_seconds}s` : 'Unavailable'}
          </strong>
        </div>
        <div>
          <span>Version</span>
          <strong>{number(rule.configuration?.version)}</strong>
        </div>
      </div>
      <div className="rule-support">
        <span className={rule.live_supported ? 'status-dot' : 'muted-dot'} />
        {rule.live_supported
          ? 'Trusted telemetry adapter supported'
          : 'Required telemetry adapter unavailable'}
      </div>
      {allowed ? (
        <Button size="sm" variant="outline" onClick={() => setEditing(!editing)}>
          {editing ? 'Cancel edit' : 'Edit configuration'}
        </Button>
      ) : (
        <span className="small secondary">
          {session.mode === 'demo'
            ? 'Read-only demo configuration'
            : 'Administrator permission required to edit'}
        </span>
      )}
      {editing && (
        <form
          className="rule-editor"
          onSubmit={(e) => {
            e.preventDefault()
            if (valid && rule.configuration)
              patch.mutate(
                {
                  enabled,
                  configuration: {
                    ...rule.configuration,
                    threshold: Number(threshold),
                    window_seconds: Number(seconds),
                  },
                },
                { onSuccess: () => setEditing(false) },
              )
          }}
        >
          <label className="stack-label">
            Threshold
            <Input
              type="number"
              step="any"
              min="0.000001"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
            />
          </label>
          <label className="stack-label">
            Window (seconds)
            <Input
              type="number"
              min="1"
              max="300"
              value={seconds}
              onChange={(e) => setSeconds(e.target.value)}
            />
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={enabled}
              disabled={!rule.live_supported && !rule.enabled}
              onChange={(e) => setEnabled(e.target.checked)}
            />
            Enabled
          </label>
          <Button disabled={!valid || patch.isPending} type="submit">
            Save reviewed configuration
          </Button>
          {patch.isError && (
            <p className="error-text" role="alert">
              {errorMessage(patch.error)}
            </p>
          )}
        </form>
      )}
    </div>
  )
}
export function Rules() {
  const [page, setPage] = useState(1)
  const rules = useResource('/api/v1/security/rules', rulesSchema, { page, page_size: 12 })
  return (
    <>
      <div className="notice subtle">
        <SlidersHorizontal size={17} />
        Rules express explicit thresholds. Optional strategies stay disabled until their required
        telemetry is trustworthy.
      </div>
      <Panel
        title="Detection policies"
        subtitle="Configuration and readiness are reported by the backend"
        action={<Pill>{number(rules.data?.total)} policies</Pill>}
      >
        <State query={rules} empty={rules.data?.rules.length === 0}>
          <div className="rules-grid">
            {rules.data?.rules.map((r) => (
              <RuleCard key={r.id + ':' + r.configuration?.version} rule={r} />
            ))}
          </div>
        </State>
        <Pagination page={page} total={rules.data?.total} size={12} onChange={setPage} />
      </Panel>
    </>
  )
}
export function ML() {
  const { params } = usePeriod()
  const [page, setPage] = useState(1)
  const model = useResource('/api/v1/ml/model', modelSchema)
  const evaluation = useResource('/api/v1/ml/evaluation', evaluationSchema)
  const anomalies = useResource('/api/v1/ml/anomalies', anomaliesSchema, {
    ...params,
    page,
    page_size: 20,
  })
  const m = model.data
  const e = evaluation.data
  const comparison = e
    ? [
        { name: 'Precision', ML: e.ml.precision, Rules: e.rules.precision },
        { name: 'Recall', ML: e.ml.recall, Rules: e.rules.recall },
        { name: 'F1', ML: e.ml.f1, Rules: e.rules.f1 },
        {
          name: 'False positive',
          ML: e.ml.false_positive_rate,
          Rules: e.rules.false_positive_rate,
        },
      ]
    : []
  return (
    <>
      <div className="notice warning">
        <CircleAlert size={18} />
        <div>
          <strong>Experimental models require context.</strong> Synthetic evaluation is not live
          production performance. Anomaly scores do not establish malicious intent.
        </div>
      </div>
      <div className="ml-top">
        <Panel
          title="Isolation Forest"
          subtitle="Model artifact readiness"
          action={<BrainCircuit size={19} />}
        >
          <State query={model}>
            <div className="detail-body">
              <div className="model-state">
                <span className="model-orbit">
                  <BrainCircuit size={28} />
                </span>
                <div>
                  <Pill
                    tone={
                      m?.state === 'ready'
                        ? 'success'
                        : m?.state === 'unavailable'
                          ? 'neutral'
                          : 'warning'
                    }
                  >
                    {m?.state ?? 'Unavailable'}
                  </Pill>
                  <p>
                    {m?.production_ready
                      ? 'Production readiness declared by artifact'
                      : 'Production readiness pending'}
                  </p>
                </div>
              </div>
              <dl className="facts">
                <div>
                  <dt>Model version</dt>
                  <dd>
                    <code>{m?.model_version ?? 'Unavailable'}</code>
                  </dd>
                </div>
                <div>
                  <dt>Data provenance</dt>
                  <dd>{m?.provenance ?? 'Unavailable'}</dd>
                </div>
                <div>
                  <dt>Feature schema</dt>
                  <dd>{m?.schema ?? 'Unavailable'}</dd>
                </div>
                <div>
                  <dt>Trained at</dt>
                  <dd>{time(m?.trained_at)}</dd>
                </div>
                <div>
                  <dt>Deployment</dt>
                  <dd>
                    {m?.deployment_enabled === undefined
                      ? 'Unavailable'
                      : m.deployment_enabled
                        ? 'Enabled by operator'
                        : 'Not enabled'}
                  </dd>
                </div>
                <div>
                  <dt>Worker freshness</dt>
                  <dd>Not established by artifact health</dd>
                </div>
              </dl>
            </div>
          </State>
        </Panel>
        <Panel
          title="Evaluation evidence"
          subtitle="Actual report metadata · independently versioned"
          action={<Pill tone="warning">{e?.provenance ?? 'Unavailable'}</Pill>}
        >
          <State query={evaluation}>
            <div className="detail-body">
              {e && (
                <>
                  <div className="eval-metrics">
                    <div>
                      <span>Precision</span>
                      <strong>{percent(e.ml.precision)}</strong>
                    </div>
                    <div>
                      <span>Recall</span>
                      <strong>{percent(e.ml.recall)}</strong>
                    </div>
                    <div>
                      <span>F1 score</span>
                      <strong>{number(e.ml.f1)}</strong>
                    </div>
                    <div>
                      <span>False-positive rate</span>
                      <strong>{percent(e.ml.false_positive_rate)}</strong>
                    </div>
                  </div>
                  <div className="eval-distribution">
                    <span>{number(e.evaluation_windows)} held-out windows</span>
                    <span>
                      {e.ml.class_distribution.normal} normal ·{' '}
                      {e.ml.class_distribution.controlled_scenario} controlled scenarios
                    </span>
                  </div>
                  <p className="small secondary">
                    Evaluated {time(e.evaluation_date)}
                    <br />
                    Report model: <code>{e.model_version}</code>
                    <br />
                    Live detection latency:{' '}
                    {e.detection_latency_seconds === null
                      ? 'not measured'
                      : `${e.detection_latency_seconds}s`}
                  </p>
                  {m?.model_version && m.model_version !== e.model_version && (
                    <div className="notice warning">
                      This report belongs to a different model version.
                    </div>
                  )}
                </>
              )}
            </div>
          </State>
        </Panel>
      </div>
      <div className="overview-charts equal">
        <Panel
          title="Rules vs. anomaly detection"
          subtitle="Same controlled evaluation events · lower false-positive rate is better"
        >
          <State query={evaluation}>{e && <ComparisonChart data={comparison} />}</State>
          <div className="panel-foot">
            Rule history: 300s. ML window: 60s. Different detection purposes; this comparison does
            not establish superiority.
          </div>
        </Panel>
        <Panel
          title="Anomaly score distribution"
          subtitle="Returned anomaly page only · 0.05-width bins"
        >
          <State query={anomalies} empty={anomalies.data?.anomalies.length === 0}>
            {anomalies.data && (
              <ScoreChart scores={anomalies.data.anomalies.map((a) => a.decision_score)} />
            )}
          </State>
          <div className="panel-foot">
            Raw decision_function scores. Lower is more unusual; normal windows are excluded from
            this endpoint.
          </div>
        </Panel>
      </div>
      <Panel
        title="Recent anomaly windows"
        subtitle="Finalized windows scored by an approved model"
      >
        <State query={anomalies} empty={anomalies.data?.anomalies.length === 0}>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Window start · UTC</th>
                  <th>Model</th>
                  <th>Raw score</th>
                  <th>Requests</th>
                  <th>Provenance</th>
                  <th>Alert</th>
                </tr>
              </thead>
              <tbody>
                {anomalies.data?.anomalies.map((a) => (
                  <tr key={a.window_id + a.model_version}>
                    <td>{time(a.window_start)}</td>
                    <td>
                      <code>{a.model_version}</code>
                    </td>
                    <td>
                      <span className="score-value">{a.decision_score.toFixed(6)}</span>
                    </td>
                    <td>{number(a.features.request_count)}</td>
                    <td>
                      <Pill tone="warning">{a.provenance}</Pill>
                    </td>
                    <td>
                      {a.alert_id ? (
                        <Link className="text-link" to={'/alerts/' + a.alert_id}>
                          Investigate →
                        </Link>
                      ) : (
                        'No linked alert'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </State>
        <Pagination page={page} total={anomalies.data?.total} onChange={setPage} />
      </Panel>
    </>
  )
}
