import Plot from 'react-plotly.js'
import { useApiData } from '../../common/hooks/useApiData'
import { ChartCard } from '../../common/components/ChartCard'
import { CHART_SLOT, useCategoricalColors } from '../../common/utils/chartColors'
import { FUEL_TYPE_GROUP_ORDER, groupFuelType } from '../data/fuelTypeGroups'
import type { GenerationMixPoint } from '../../common/types'

const SLOT_BY_GROUP: Record<(typeof FUEL_TYPE_GROUP_ORDER)[number], number> = {
  'Wind onshore': CHART_SLOT.blue,
  Biomass: CHART_SLOT.green,
  Hydro: CHART_SLOT.magenta,
  Solar: CHART_SLOT.yellow,
  'Wind offshore': CHART_SLOT.aqua,
  Gas: CHART_SLOT.orange,
  Nuclear: CHART_SLOT.violet,
  Other: CHART_SLOT.red,
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
export function GenerationMixChart() {
  const { data, error, isLoading } = useApiData<GenerationMixPoint[]>(
    '/api/dashboard/generation-mix',
  )
  const colors = useCategoricalColors(FUEL_TYPE_GROUP_ORDER.map((group) => SLOT_BY_GROUP[group]))
  const hasData = Boolean(data && data.length > 0)
  const { timestamps, series } = pivotByFuelTypeGroup(data ?? [])

  return (
    <ChartCard title="Generation mix" isLoading={isLoading} hasData={hasData} error={error}>
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
