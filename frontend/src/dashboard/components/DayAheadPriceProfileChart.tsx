import Plot from 'react-plotly.js'
import { useApiData } from '../../common/hooks/useApiData'
import { ChartCard } from '../../common/components/ChartCard'
import { CHART_SLOT, useCategoricalColor } from '../../common/utils/chartColors'
import type { ResolvedDateRange } from '../../common/utils/dateRange'
import type { DayAheadPriceProfilePoint } from '../../common/types'

interface DayAheadPriceProfileChartProps {
  range: ResolvedDateRange
}

/** Settlement period 1 covers 00:00-00:30, period 2 covers 00:30-01:00, and so on. */
function periodToTimeLabel(settlementPeriod: number): string {
  const minutesFromMidnight = (settlementPeriod - 1) * 30
  const hours = Math.floor(minutesFromMidnight / 60) % 24
  const minutes = minutesFromMidnight % 60
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`
}

/**
 * The average shape of the GB day-ahead price across a day, aggregated over
 * every day in the selected range — cheap overnight, a morning ramp, and an
 * evening peak. This is the pattern a VPP battery schedules its
 * charge/discharge cycle around, rather than reacting to any single day's
 * price. The error bars are one standard deviation across the days in
 * range: a wide bar means that settlement period's price is unpredictable
 * day-to-day, which matters as much as the average when sizing a strategy.
 */
export function DayAheadPriceProfileChart({ range }: DayAheadPriceProfileChartProps) {
  const { data, error, isLoading } = useApiData<DayAheadPriceProfilePoint[]>(
    `/api/dashboard/day-ahead-price-profile?start=${range.start}&end=${range.end}`,
    range.isLive ? undefined : 0,
  )
  const color = useCategoricalColor(CHART_SLOT.orange)
  const hasData = Boolean(data && data.length > 0)
  const sorted = [...(data ?? [])].sort((a, b) => a.settlementPeriod - b.settlementPeriod)

  return (
    <ChartCard
      title="Average daily price profile"
      isLoading={isLoading}
      hasData={hasData}
      error={error}
    >
      <Plot
        data={[
          {
            x: sorted.map((d) => periodToTimeLabel(d.settlementPeriod)),
            y: sorted.map((d) => d.meanPrice),
            error_y: {
              type: 'data',
              array: sorted.map((d) => d.stdPrice),
              visible: true,
              color,
              thickness: 1,
              width: 2,
            },
            type: 'bar',
            marker: { color },
            name: 'Mean day-ahead price (£/MWh)',
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
          xaxis: { title: { text: 'Time of day' } },
          yaxis: { title: { text: '£/MWh' } },
        }}
        useResizeHandler
        style={{ width: '100%' }}
        config={{ displayModeBar: false }}
      />
    </ChartCard>
  )
}
