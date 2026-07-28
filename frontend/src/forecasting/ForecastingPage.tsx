import { PageLayout } from '../common/components/PageLayout'
import { ExplainerPanel } from '../common/components/ExplainerPanel'
import { DayAheadForecastChart } from './components/DayAheadForecastChart'
import { ModelInfoPanel } from './components/ModelInfoPanel'
import { BacktestPanel } from './components/BacktestPanel'

export function ForecastingPage() {
  return (
    <PageLayout
      title="Price forecasting"
      description="Forecasting tomorrow's GB day-ahead price with quantile regression."
    >
      <ExplainerPanel title="What is quantile regression?">
        <p>
          A normal regression model predicts a single number — &quot;tomorrow at 18:00 will be
          £145/MWh&quot;. That&apos;s not very useful on its own: a virtual power plant (VPP)
          scheduling a battery around it has no idea how much to trust that number.{' '}
          <strong>Quantile regression</strong> instead predicts a range: the 10th percentile
          (&quot;probably won&apos;t go below this&quot;), the 50th (the median, a best central
          guess), and the 90th (&quot;probably won&apos;t go above this&quot;). It does this by
          training a separate model for each percentile, each minimizing a different, asymmetric
          version of the error — one that penalizes under-prediction more heavily for a high
          percentile, and over-prediction more heavily for a low one (called{' '}
          <strong>pinball loss</strong>). The result is a band, not a point: exactly the shape of
          uncertainty a VPP needs to decide how aggressively to commit a battery&apos;s
          charge/discharge cycle.
        </p>
      </ExplainerPanel>

      <ExplainerPanel title="How is this model built?">
        <p>
          The model is a gradient-boosted quantile regression (scikit-learn&apos;s{' '}
          <code className="text-xs">GradientBoostingRegressor</code>, one independently-fit model
          per quantile), trained only on the day-ahead price&apos;s own history plus calendar
          features — see the model card below for the exact feature list. A few honest limitations
          worth stating plainly rather than glossing over:
        </p>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>
            No demand or wind forecasts are used as inputs yet — the dashboard only has{' '}
            <em>outturn</em> data for those, not forecasts, and using tomorrow&apos;s actual demand
            to predict tomorrow&apos;s price would be leaking the future into the model. The model
            can only react to calendar and price-history patterns, not to a genuinely new piece of
            information like an unexpected cold snap or a wind lull.
          </li>
          <li>
            The two UK clock-change days each year (46 or 50 settlement periods instead of 48) have
            very little price history at their extra/missing periods, so predictions there are the
            least reliable of the year.
          </li>
          <li>
            Model quality below is measured on a single fixed holdout window, not a full
            walk-forward backtest that retrains every day — cheaper to compute, but a real
            simplification that could make performance look better or worse than the long-run
            average, depending on whether that window happened to be calm or volatile.
          </li>
        </ul>
      </ExplainerPanel>

      <DayAheadForecastChart />
      <ModelInfoPanel />
      <BacktestPanel />
    </PageLayout>
  )
}
