import { PageLayout } from '../common/components/PageLayout'
import { ExplainerPanel } from '../common/components/ExplainerPanel'

export function VppPage() {
  return (
    <PageLayout
      title="VPP optimisation"
      description="Optimising a virtual power plant (VPP) against price forecasts and asset constraints."
    >
      <ExplainerPanel title="What is a virtual power plant?">
        <p>
          {/* TODO: explain VPPs and the optimisation problem being solved */}
          Explanation coming soon.
        </p>
      </ExplainerPanel>
      <p className="text-sm text-slate-500 dark:text-slate-500">
        Optimisation results and dispatch schedules will appear here.
      </p>
    </PageLayout>
  )
}
