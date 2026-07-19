import { PageLayout } from '../common/components/PageLayout'
import { ExplainerPanel } from '../common/components/ExplainerPanel'

export function ForecastingPage() {
  return (
    <PageLayout
      title="Price forecasting"
      description="Forecasting energy prices using quantile regression."
    >
      <ExplainerPanel title="What is quantile regression?">
        <p>
          {/* TODO: explain quantile regression and why it suits price forecasting */}
          Explanation coming soon.
        </p>
      </ExplainerPanel>
      <p className="text-sm text-slate-500 dark:text-slate-500">
        Forecast charts and model outputs will appear here.
      </p>
    </PageLayout>
  )
}
