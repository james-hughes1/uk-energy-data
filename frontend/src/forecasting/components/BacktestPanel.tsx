import { useApiData } from '../../common/hooks/useApiData'
import { ChartCard } from '../../common/components/ChartCard'
import type { BacktestResponse } from '../../common/types'

/**
 * How good the model actually is, checked against a holdout window it never
 * trained on: pinball loss and calibration (empirical vs. nominal coverage)
 * per quantile, plus a head-to-head comparison against the naive "same
 * period last week" persistence baseline at the median. A single fixed
 * holdout split, not a full walk-forward backtest — see the explainer above
 * for why that's a reasonable simplification for a first version.
 */
export function BacktestPanel() {
  const { data, error, isLoading } = useApiData<BacktestResponse>('/api/forecasting/backtest', 0)
  const hasData = Boolean(data)
  const beatsBaseline = data
    ? data.modelPinballLossP50 < data.persistenceBaselinePinballLossP50
    : false
  const improvementPct = data
    ? Math.round((1 - data.modelPinballLossP50 / data.persistenceBaselinePinballLossP50) * 100)
    : 0

  return (
    <ChartCard
      title="How good is this model?"
      isLoading={isLoading}
      hasData={hasData}
      error={error}
      note={data ? `Holdout: ${data.holdoutStart} → ${data.holdoutEnd}` : undefined}
    >
      {data && (
        <div className="flex flex-col gap-4 text-sm text-slate-700 dark:text-slate-300">
          <p>
            {beatsBaseline ? (
              <>
                At the median, the model beats the naive &quot;same period last week&quot; baseline
                by about <strong>{improvementPct}%</strong> (pinball loss{' '}
                {data.modelPinballLossP50.toFixed(2)} vs.{' '}
                {data.persistenceBaselinePinballLossP50.toFixed(2)}
                ).
              </>
            ) : (
              <>
                At the median, the model does <strong>not</strong> beat the naive &quot;same period
                last week&quot; baseline (pinball loss {data.modelPinballLossP50.toFixed(2)} vs.{' '}
                {data.persistenceBaselinePinballLossP50.toFixed(2)}) — a real result worth taking at
                face value, not smoothing over.
              </>
            )}
          </p>

          <div className="overflow-x-auto">
            <table className="w-full min-w-max text-left">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 dark:border-slate-800 dark:text-slate-400">
                  <th className="py-1 pr-4 font-medium">Quantile</th>
                  <th className="py-1 pr-4 font-medium">Pinball loss</th>
                  <th className="py-1 pr-4 font-medium">Nominal coverage</th>
                  <th className="py-1 font-medium">Empirical coverage</th>
                </tr>
              </thead>
              <tbody>
                {data.quantileMetrics.map((metric) => (
                  <tr
                    key={metric.quantile}
                    className="border-b border-slate-100 dark:border-slate-800/50"
                  >
                    <td className="py-1 pr-4">p{metric.quantile * 100}</td>
                    <td className="py-1 pr-4">{metric.pinballLoss.toFixed(2)}</td>
                    <td className="py-1 pr-4">{(metric.nominalCoverage * 100).toFixed(0)}%</td>
                    <td className="py-1">{(metric.empiricalCoverage * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-500">
            Empirical coverage is the share of actual holdout prices at or below that
            quantile&apos;s prediction — a well-calibrated p10 should see this land near 10%.
          </p>
        </div>
      )}
    </ChartCard>
  )
}
