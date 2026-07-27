import Plot from 'react-plotly.js'
import { useApiData } from '../../common/hooks/useApiData'
import { ChartCard } from '../../common/components/ChartCard'
import { CHART_SLOT, useCategoricalColors } from '../../common/utils/chartColors'
import { FUEL_TYPE_GROUP_ORDER, groupFuelType } from '../data/fuelTypeGroups'
import type { ResolvedDateRange } from '../../common/utils/dateRange'
import type { GenerationMixPoint } from '../../common/types'

interface GenerationMixChartProps {
  range: ResolvedDateRange
}

const SLOT_BY_GROUP: Record<(typeof FUEL_TYPE_GROUP_ORDER)[number], number> = {
  Wind: CHART_SLOT.blue,
  Biomass: CHART_SLOT.green,
  Hydro: CHART_SLOT.magenta,
  Solar: CHART_SLOT.yellow,
  Coal: CHART_SLOT.aqua,
  Gas: CHART_SLOT.orange,
  Nuclear: CHART_SLOT.violet,
  Other: CHART_SLOT.red,
}

// Wind and solar are metered near-real-time; everything else comes from a
// dataset that lags real time by a couple of weeks (see the backend's
// `_lagging_data_cutoff`). The backend already drops unpublished rows for
// those fuel types rather than sending fake zeros, so a gap here is real —
// worth flagging, or the chart's trailing edge would silently look like
// "only wind and solar were generating".
const NEAR_REAL_TIME_GROUPS = new Set(['Wind', 'Solar'])

function describeLaggingDataGap(points: GenerationMixPoint[]): string | undefined {
  if (points.length === 0) return undefined

  let overallLatest = points[0].timestamp
  let laggingLatest: string | null = null
  for (const point of points) {
    if (point.timestamp > overallLatest) overallLatest = point.timestamp
    if (!NEAR_REAL_TIME_GROUPS.has(groupFuelType(point.fuelType))) {
      if (laggingLatest === null || point.timestamp > laggingLatest) laggingLatest = point.timestamp
    }
  }

  if (laggingLatest === null) {
    return "Gas, nuclear, and other non-weather sources aren't published yet for this range"
  }
  const gapMs = new Date(overallLatest).getTime() - new Date(laggingLatest).getTime()
  if (gapMs <= 24 * 60 * 60 * 1000) return undefined
  return `Gas, nuclear, etc. only published up to ${laggingLatest.slice(0, 10)}`
}

/** Pivots flat (timestamp, fuelType, quantity) rows into one series per fuel-type group. */
function pivotByFuelTypeGroup(points: GenerationMixPoint[]) {
  const timestamps = [...new Set(points.map((p) => p.timestamp))].sort()
  const quantityByGroupAndTimestamp = new Map<string, Map<string, number>>()

  for (const point of points) {
    const group = groupFuelType(point.fuelType)
    const byTimestamp = quantityByGroupAndTimestamp.get(group) ?? new Map<string, number>()
    byTimestamp.set(point.timestamp, (byTimestamp.get(point.timestamp) ?? 0) + point.quantityMw)
    quantityByGroupAndTimestamp.set(group, byTimestamp)
  }

  return {
    timestamps,
    series: FUEL_TYPE_GROUP_ORDER.map((group) => ({
      group,
      values: timestamps.map((t) => quantityByGroupAndTimestamp.get(group)?.get(t) ?? 0),
    })),
  }
}

/**
 * GB generation output broken down by fuel type, from Elexon's actual
 * generation per PSR type endpoint (AGPT/B1620) — the mix of gas, nuclear,
 * wind, solar and more that's meeting demand right now.
 */
export function GenerationMixChart({ range }: GenerationMixChartProps) {
  const { data, error, isLoading } = useApiData<GenerationMixPoint[]>(
    `/api/dashboard/generation-mix?start=${range.start}&end=${range.end}`,
    range.isLive ? undefined : 0,
  )
  const colors = useCategoricalColors(FUEL_TYPE_GROUP_ORDER.map((group) => SLOT_BY_GROUP[group]))
  const hasData = Boolean(data && data.length > 0)
  const { timestamps, series } = pivotByFuelTypeGroup(data ?? [])

  return (
    <ChartCard
      title="Generation mix"
      isLoading={isLoading}
      hasData={hasData}
      error={error}
      note={data ? describeLaggingDataGap(data) : undefined}
    >
      <Plot
        data={series.map(({ group, values }, i) => ({
          x: timestamps,
          y: values,
          type: 'scatter',
          mode: 'lines',
          stackgroup: 'generation',
          line: { color: colors[i], width: 1 },
          name: group,
        }))}
        layout={{
          autosize: true,
          height: 360,
          margin: { l: 60, r: 20, t: 10, b: 40 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          legend: { orientation: 'h', y: -0.25 },
          hovermode: 'x unified',
          xaxis: { title: { text: 'Time' } },
          yaxis: { title: { text: 'MW' } },
        }}
        useResizeHandler
        style={{ width: '100%' }}
        config={{ displayModeBar: false }}
      />
    </ChartCard>
  )
}
