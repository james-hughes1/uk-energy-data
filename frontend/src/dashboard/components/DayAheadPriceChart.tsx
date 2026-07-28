import Plot from 'react-plotly.js'
import { useApiData } from '../../common/hooks/useApiData'
import { ChartCard } from '../../common/components/ChartCard'
import { CHART_SLOT, useCategoricalColor } from '../../common/utils/chartColors'
import type { ResolvedDateRange } from '../../common/utils/dateRange'
import type { DayAheadPricePoint } from '../../common/types'

interface DayAheadPriceChartProps {
  range: ResolvedDateRange
}

/**
 * GB day-ahead price: the volume weighted average of the market index data
 * (MID) providers (APX, N2EX), the closest free proxy for the day-ahead
 * auction clearing price. Unlike the imbalance price, this reflects what was
 * actually contracted the day before delivery — the signal a VPP schedules
 * its battery cycle against, rather than the real-time cost of deviating
 * from that schedule.
 */
export function DayAheadPriceChart({ range }: DayAheadPriceChartProps) {
  const { data, error, isLoading } = useApiData<DayAheadPricePoint[]>(
    `/api/dashboard/day-ahead-price?start=${range.start}&end=${range.end}`,
    range.isLive ? undefined : 0,
  )
  const color = useCategoricalColor(CHART_SLOT.green)
  const hasData = Boolean(data && data.length > 0)

  return (
    <ChartCard title="Day-ahead price" isLoading={isLoading} hasData={hasData} error={error}>
      <Plot
        data={[
          {
            x: data?.map((d) => d.timestamp) ?? [],
            y: data?.map((d) => d.price) ?? [],
            type: 'scatter',
            mode: 'lines',
            line: { color, width: 2 },
            name: 'Day-ahead price (£/MWh)',
          },
        ]}
        layout={{
          autosize: true,
          height: 320,
          margin: { l: 50, r: 20, t: 10, b: 40 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          showlegend: false,
          hovermode: 'x unified',
          xaxis: { title: { text: 'Time' } },
          yaxis: { title: { text: '£/MWh' } },
        }}
        useResizeHandler
        style={{ width: '100%' }}
        config={{ displayModeBar: false }}
      />
    </ChartCard>
  )
}
