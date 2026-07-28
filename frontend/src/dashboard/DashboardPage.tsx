import { useState } from 'react'
import { PageLayout } from '../common/components/PageLayout'
import { ExplainerPanel } from '../common/components/ExplainerPanel'
import { DateRangeControl } from '../common/components/DateRangeControl'
import { resolveDateRangeSelection, type DateRangeSelection } from '../common/utils/dateRange'
import { ImbalancePriceChart } from './components/ImbalancePriceChart'
import { DemandChart } from './components/DemandChart'
import { GenerationMixChart } from './components/GenerationMixChart'
import { DayAheadPriceChart } from './components/DayAheadPriceChart'
import { DayAheadPriceProfileChart } from './components/DayAheadPriceProfileChart'

export function DashboardPage() {
  const [rangeSelection, setRangeSelection] = useState<DateRangeSelection>({
    type: 'preset',
    key: 'last24h',
  })
  const range = resolveDateRangeSelection(rangeSelection)

  return (
    <PageLayout
      title="Live grid dashboard"
      description="Live UK power grid data — day-ahead and imbalance prices, demand, and generation mix, from Elexon's BMRS Insights API."
    >
      <DateRangeControl selection={rangeSelection} onChange={setRangeSelection} />

      <ExplainerPanel title="What is the day-ahead price?">
        <p>
          Most GB electricity is bought and sold in the <strong>day-ahead market</strong>: for each
          half-hourly period of tomorrow, generators and suppliers submit bids/offers that clear in
          an auction today, producing a single price per period. This chart shows that price — the
          volume-weighted average across the exchange feeds Elexon publishes (APX and N2EX), the
          closest free proxy for the auction result. It&apos;s a much bigger, more predictable
          signal than the imbalance price below, and it&apos;s the one a virtual power plant (VPP)
          mainly schedules against: charge the battery in cheap periods, sell it back in expensive
          ones.
        </p>
      </ExplainerPanel>
      <DayAheadPriceChart range={range} />
      <DayAheadPriceProfileChart range={range} />

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
      <ImbalancePriceChart range={range} />

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
      <DemandChart range={range} />

      <ExplainerPanel title="What is the generation mix?">
        <p>
          This is what&apos;s actually generating the electricity meeting that demand right now,
          broken down by fuel type — dispatchable fossil gas, steady nuclear, and weather-dependent
          wind and solar. Over a day, watch how the mix reshuffles between a calm, sunny afternoon
          and a windy night. Zoomed out to &quot;all time&quot;, it tells a bigger story: coal, a
          major source as recently as 2016, all but disappears within a few years — one of the
          clearest signals of the UK&apos;s shift away from fossil fuels.
        </p>
      </ExplainerPanel>
      <GenerationMixChart range={range} />
    </PageLayout>
  )
}
