import Plot from 'react-plotly.js'
import { useMockData } from '../../common/hooks/useMockData'
import { MOCK_IMBALANCE_PRICE } from '../data/mockGridData'

/**
 * Placeholder chart of the GB imbalance price, the price suppliers pay (or
 * are paid) for being out of balance with their contracted position. Will be
 * wired up to live data from the dashboard API once it exists.
 */
export function ImbalancePriceChart() {
  const data = useMockData(
    MOCK_IMBALANCE_PRICE.points,
    MOCK_IMBALANCE_PRICE.baseValue,
    MOCK_IMBALANCE_PRICE.amplitude,
  )

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <h2 className="mb-2 text-sm font-medium text-slate-700 dark:text-slate-300">
        Imbalance price (mock data)
      </h2>
      <Plot
        data={[
          {
            x: data.map((d) => d.timestamp),
            y: data.map((d) => d.value),
            type: 'scatter',
            mode: 'lines',
            line: { color: '#2563eb' },
            name: 'Imbalance price (£/MWh)',
          },
        ]}
        layout={{
          autosize: true,
          height: 320,
          margin: { l: 50, r: 20, t: 10, b: 40 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          xaxis: { title: { text: 'Time' } },
          yaxis: { title: { text: '£/MWh' } },
        }}
        useResizeHandler
        style={{ width: '100%' }}
        config={{ displayModeBar: false }}
      />
    </div>
  )
}
