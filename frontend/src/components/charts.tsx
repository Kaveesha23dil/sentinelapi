import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Legend,
} from 'recharts'

const tooltip = {
  background: '#101b2c',
  border: '1px solid #304059',
  borderRadius: 8,
  color: '#f8fafc',
  fontSize: 12,
}
const axis = { fill: '#94a3b8', fontSize: 11 }
export function TrafficChart({ points }: { points: { timestamp: string; requests: number }[] }) {
  return (
    <div
      className="chart"
      role="img"
      aria-label={`Traffic chart with ${points.length} observed time buckets; missing buckets do not establish zero traffic.`}
    >
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={points} margin={{ top: 12, right: 16, bottom: 4, left: -20 }}>
          <defs>
            <linearGradient id="traffic-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.01} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#253147" vertical={false} strokeDasharray="3 4" />
          <XAxis
            dataKey="timestamp"
            tick={axis}
            tickLine={false}
            axisLine={false}
            minTickGap={48}
            tickFormatter={(v) =>
              new Date(v).toLocaleTimeString('en-GB', {
                hour: '2-digit',
                minute: '2-digit',
                timeZone: 'UTC',
              })
            }
          />
          <YAxis tick={axis} tickLine={false} axisLine={false} allowDecimals={false} />
          <Tooltip
            contentStyle={tooltip}
            labelFormatter={(v) =>
              `${new Date(String(v)).toLocaleString('en-GB', { timeZone: 'UTC' })} UTC`
            }
          />
          <Area
            type="linear"
            dataKey="requests"
            name="Requests"
            stroke="#60a5fa"
            strokeWidth={2}
            fill="url(#traffic-fill)"
            dot={false}
            activeDot={{ r: 4 }}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
export function StatusChart({ breakdown }: { breakdown: Record<string, number> }) {
  const groups = [
    { name: '2xx · Successful', color: '#3b82f6', value: 0 },
    { name: '4xx · Client error', color: '#f59e0b', value: 0 },
    { name: '5xx · Server error', color: '#ef4444', value: 0 },
    { name: 'Other status', color: '#94a3b8', value: 0 },
  ]
  Object.entries(breakdown).forEach(([code, n]) => {
    groups[
      code.startsWith('2') ? 0 : code.startsWith('4') ? 1 : code.startsWith('5') ? 2 : 3
    ].value += n
  })
  const total = groups.reduce((s, g) => s + g.value, 0)
  return (
    <div className="status-chart">
      <div
        className="donut"
        role="img"
        aria-label={groups.map((g) => `${g.name}: ${g.value}`).join(', ')}
      >
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={groups.filter((g) => g.value > 0)}
              innerRadius="70%"
              outerRadius="94%"
              dataKey="value"
              paddingAngle={3}
              stroke="none"
              isAnimationActive={false}
            >
              {groups
                .filter((g) => g.value > 0)
                .map((g) => (
                  <Cell key={g.name} fill={g.color} />
                ))}
            </Pie>
            <Tooltip contentStyle={tooltip} />
          </PieChart>
        </ResponsiveContainer>
        <div className="donut-center">
          <strong>{total}</strong>
          <span>requests</span>
        </div>
      </div>
      <div className="status-legend">
        {groups
          .filter((g) => g.value > 0)
          .map((g) => (
            <div key={g.name}>
              <span>
                <i style={{ background: g.color }} />
                {g.name}
              </span>
              <strong>{g.value.toLocaleString()}</strong>
            </div>
          ))}
      </div>
    </div>
  )
}
export function ComparisonChart({
  data,
}: {
  data: { name: string; ML: number | null; Rules: number | null }[]
}) {
  return (
    <div
      className="chart short-chart"
      role="img"
      aria-label="Measured evaluation comparison; lower false-positive rate is better"
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ left: -25, right: 8, top: 12 }}>
          <CartesianGrid vertical={false} stroke="#253147" />
          <XAxis dataKey="name" tick={axis} axisLine={false} tickLine={false} />
          <YAxis domain={[0, 1]} tick={axis} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={tooltip} />
          <Legend />
          <Bar dataKey="ML" fill="#3b82f6" radius={[3, 3, 0, 0]} isAnimationActive={false} />
          <Bar dataKey="Rules" fill="#94a3b8" radius={[3, 3, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
export function ScoreChart({ scores }: { scores: number[] }) {
  const bins = new Map<string, number>()
  scores.forEach((s) => {
    const key = (Math.floor(s * 20) / 20).toFixed(2)
    bins.set(key, (bins.get(key) ?? 0) + 1)
  })
  const data = [...bins]
    .sort((a, b) => Number(a[0]) - Number(b[0]))
    .map(([score, count]) => ({ score, count }))
  return (
    <div
      className="chart short-chart"
      role="img"
      aria-label="Raw negative decision score histogram for returned anomaly page only"
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid vertical={false} stroke="#253147" />
          <XAxis dataKey="score" tick={axis} />
          <YAxis allowDecimals={false} tick={axis} />
          <Tooltip contentStyle={tooltip} />
          <Bar
            dataKey="count"
            name="Anomaly windows"
            fill="#a78bfa"
            radius={[4, 4, 0, 0]}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
