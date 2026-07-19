import { PageLayout } from '../common/components/PageLayout'
import { ExplainerPanel } from '../common/components/ExplainerPanel'
import { ImbalancePriceChart } from './components/ImbalancePriceChart'

export function DashboardPage() {
  return (
    <PageLayout
      title="Live grid dashboard"
      description="Live UK power grid data — imbalance price, demand, and more."
    >
      <ExplainerPanel title="What is the imbalance price?">
        <p>
          {/* TODO: explain imbalance pricing and why it matters for grid balancing */}
          Explanation coming soon.
        </p>
      </ExplainerPanel>
      <ImbalancePriceChart />
    </PageLayout>
  )
}
