import Plot from 'react-plotly.js'
import { useApiData } from '../../common/hooks/useApiData'
import { ChartCard } from '../../common/components/ChartCard'
import { CHART_SLOT, useCategoricalColor, withAlpha } from '../../common/utils/chartColors'
import { periodToTimeLabel } from '../../common/utils/settlementPeriod'
import type { DayAheadForecastResponse } from '../../common/types'

/**
 * Tomorrow's predicted day-ahead price as a quantile "fan": a shaded 10th-90th
 * percentile band with the median drawn on top. The band is the point — a VPP
 * schedules a battery against the median line, but sizes its risk against how
 * wide the shaded range is at each time of day. Refetches only once (the
 * forecast changes at most once a day, when the model retrains), unlike the
 * live dashboard charts.
 */
export function DayAheadForecastChart() {
  const { data, error, isLoading } = useApiData<DayAheadForecastResponse>(
    '/api/forecasting/day-ahead-forecast',
    0,
  )
  const color = useCategoricalColor(CHART_SLOT.blue)
  const points = data?.points ?? []
  const hasData = points.length > 0
  const sorted = [...points].sort((a, b) => a.settlementPeriod - b.settlementPeriod)
  const labels = sorted.map((d) => periodToTimeLabel(d.settlementPeriod))

  return (
    <ChartCard
      title={
        data ? `Predicted day-ahead price for ${data.forecastDate}` : 'Predicted day-ahead price'
      }
      isLoading={isLoading}
      hasData={hasData}
      error={error}
    >
      <Plot
        data={[
          {
            x: labels,
            y: sorted.map((d) => d.p90),
            type: 'scatter',
            mode: 'lines',
            line: { width: 0 },
            fill: 'none',
            showlegend: false,
            name: '90th percentile',
          },
          {
            x: labels,
            y: sorted.map((d) => d.p10),
            type: 'scatter',
            mode: 'lines',
            line: { width: 0 },
            fill: 'tonexty',
            fillcolor: withAlpha(color, 0.18),
            showlegend: false,
            name: '10th percentile',
          },
          {
            x: labels,
            y: sorted.map((d) => d.p50),
            type: 'scatter',
            mode: 'lines',
            line: { color, width: 2 },
            name: 'Median (p50)',
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
