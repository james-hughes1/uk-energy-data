import Plot from 'react-plotly.js'
import { useApiData } from '../../common/hooks/useApiData'
import { ChartCard } from '../../common/components/ChartCard'
import { CHART_SLOT, useCategoricalColors } from '../../common/utils/chartColors'
import type { ResolvedDateRange } from '../../common/utils/dateRange'
import type { DemandPoint } from '../../common/types'

interface DemandChartProps {
  range: ResolvedDateRange
}

/**
 * GB national demand outturn: INDO (initial National Demand outturn) vs
 * ITSDO (initial Transmission System Demand outturn, which additionally
 * accounts for transmission losses, pumped storage, and interconnectors).
 * Half-hourly for short ranges; resampled to a daily mean for longer ones.
 */
export function DemandChart({ range }: DemandChartProps) {
  const { data, error, isLoading } = useApiData<DemandPoint[]>(
    `/api/dashboard/demand?start=${range.start}&end=${range.end}`,
    range.isLive ? undefined : 0,
  )
  const [nationalColor, transmissionColor] = useCategoricalColors([
    CHART_SLOT.blue,
    CHART_SLOT.violet,
  ])
  const hasData = Boolean(data && data.length > 0)

  return (
    <ChartCard title="National demand" isLoading={isLoading} hasData={hasData} error={error}>
      <Plot
        data={[
          {
            x: data?.map((d) => d.timestamp) ?? [],
            y: data?.map((d) => d.nationalDemandMw) ?? [],
            type: 'scatter',
            mode: 'lines',
            line: { color: nationalColor, width: 2 },
            name: 'National demand (INDO)',
          },
          {
            x: data?.map((d) => d.timestamp) ?? [],
            y: data?.map((d) => d.transmissionSystemDemandMw) ?? [],
            type: 'scatter',
            mode: 'lines',
            line: { color: transmissionColor, width: 2 },
            name: 'Transmission system demand (ITSDO)',
          },
        ]}
        layout={{
          autosize: true,
          height: 320,
          margin: { l: 60, r: 20, t: 10, b: 40 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          legend: { orientation: 'h', y: -0.2 },
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
