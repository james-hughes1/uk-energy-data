import { PageLayout } from '../common/components/PageLayout'
import { ExplainerPanel } from '../common/components/ExplainerPanel'
import { ImbalancePriceChart } from './components/ImbalancePriceChart'
import { DemandChart } from './components/DemandChart'
import { GenerationMixChart } from './components/GenerationMixChart'

export function DashboardPage() {
  return (
    <PageLayout
      title="Live grid dashboard"
      description="Live UK power grid data — imbalance price, demand, and generation mix, from Elexon's BMRS Insights API."
    >
      <ExplainerPanel title="What is the imbalance price?">
        <p>
          Great Britain&apos;s grid has to stay balanced second-by-second: supply must match demand.
          Generators and suppliers submit a contracted position for each 30-minute settlement
          period, and if they end up over- or under-delivering, National Energy System Operator
          (NESO) balances the difference using the balancing mechanism. The{' '}
          <strong>imbalance price</strong> (the system sell/buy price here) is what out-of-position
          parties pay, or are paid, for that gap — so it spikes when the system is under stress and
          stays low when supply and demand are easy to match.
        </p>
      </ExplainerPanel>
      <ImbalancePriceChart />

      <ExplainerPanel title="What is national demand?">
        <p>
          <strong>INDO</strong> (Initial National Demand Outturn) is the half-hourly demand metered
          on the transmission network, before accounting for things like pumped storage and
          interconnector flows. <strong>ITSDO</strong> (Initial Transmission System Demand Outturn)
          adds those back in, so it&apos;s usually a little higher — the gap between the two lines
          is a rough proxy for how much pumped hydro and interconnector trading is propping up (or
          draining) the system at that moment.
        </p>
      </ExplainerPanel>
      <DemandChart />

      <ExplainerPanel title="What is the generation mix?">
        <p>
          This is what&apos;s actually generating the electricity meeting that demand right now,
          broken down by fuel type — dispatchable fossil gas, steady nuclear, and weather-dependent
          wind and solar. It&apos;s the clearest picture of the UK&apos;s ongoing shift away from
          fossil fuels: watch how the mix reshuffles between a calm, sunny afternoon and a windy
          night.
        </p>
      </ExplainerPanel>
      <GenerationMixChart />
    </PageLayout>
  )
}
