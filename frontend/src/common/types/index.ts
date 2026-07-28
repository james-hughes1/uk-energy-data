/** A single (timestamp, value) sample, the common shape for time-series data across pages. */
export interface TimeSeriesPoint {
  timestamp: string
  value: number
}

/**
 * One settlement period's system prices — the cost of the grid being out of
 * balance. `settlementPeriod` is null once resampled to a daily/weekly mean
 * over wider ranges, where the period number isn't meaningful any more.
 */
export interface ImbalancePricePoint {
  timestamp: string
  settlementPeriod: number | null
  systemSellPrice: number
  systemBuyPrice: number
  netImbalanceVolume: number
}

/** One settlement period's national demand outturn. */
export interface DemandPoint {
  timestamp: string
  nationalDemandMw: number
  transmissionSystemDemandMw: number
}

/** A single fuel type's generation output for one settlement period. */
export interface GenerationMixPoint {
  timestamp: string
  fuelType: string
  quantityMw: number
}
