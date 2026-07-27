import Plot from 'react-plotly.js'
import { useApiData } from '../../common/hooks/useApiData'
import { ChartCard } from '../../common/components/ChartCard'
import { CHART_SLOT, useCategoricalColor } from '../../common/utils/chartColors'
import type { ImbalancePricePoint } from '../../common/types'

/**
 * The GB imbalance price: the system buy/sell price suppliers pay (or are
 * paid) per MWh for being out of balance with their contracted position,
 * from Elexon's settlement system prices (DISEBSP).
 */
export function ImbalancePriceChart() {
  const { data, error, isLoading } = useApiData<ImbalancePricePoint[]>(
    '/api/dashboard/imbalance-price',
  )
  const color = useCategoricalColor(CHART_SLOT.blue)
  const hasData = Boolean(data && data.length > 0)

  return (
    <ChartCard title="Imbalance price" isLoading={isLoading} hasData={hasData} error={error}>
      <Plot
        data={[
          {
            x: data?.map((d) => d.timestamp) ?? [],
            y: data?.map((d) => d.systemSellPrice) ?? [],
            type: 'scatter',
            mode: 'lines',
            line: { color, width: 2 },
            name: 'System sell price (£/MWh)',
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
