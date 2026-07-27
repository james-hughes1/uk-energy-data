import Plot from 'react-plotly.js'
import { useApiData } from '../../common/hooks/useApiData'
import { ChartCard } from '../../common/components/ChartCard'
import { CHART_SLOT, useCategoricalColor } from '../../common/utils/chartColors'
import { IMBALANCE_PRICE_MAX_DAYS, type ResolvedDateRange } from '../../common/utils/dateRange'
import type { ImbalancePricePoint } from '../../common/types'

interface ImbalancePriceChartProps {
  range: ResolvedDateRange
}

function daysBetween(start: string, end: string): number {
  return Math.round((new Date(end).getTime() - new Date(start).getTime()) / 86_400_000)
}

/**
 * The GB imbalance price: the system buy/sell price suppliers pay (or are
 * paid) per MWh for being out of balance with their contracted position,
 * from Elexon's settlement system prices (DISEBSP). Unlike demand and
 * generation, this data source has no bulk/range endpoint, so the backend
 * caps it at the last `IMBALANCE_PRICE_MAX_DAYS` days of whatever range is
 * requested.
 */
export function ImbalancePriceChart({ range }: ImbalancePriceChartProps) {
  const { data, error, isLoading } = useApiData<ImbalancePricePoint[]>(
    `/api/dashboard/imbalance-price?start=${range.start}&end=${range.end}`,
    range.isLive ? undefined : 0,
  )
  const color = useCategoricalColor(CHART_SLOT.blue)
  const hasData = Boolean(data && data.length > 0)
  const isClamped = daysBetween(range.start, range.end) > IMBALANCE_PRICE_MAX_DAYS

  return (
    <ChartCard
      title="Imbalance price"
      isLoading={isLoading}
      hasData={hasData}
      error={error}
      note={isClamped ? `Limited to the last ${IMBALANCE_PRICE_MAX_DAYS} days` : undefined}
    >
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
