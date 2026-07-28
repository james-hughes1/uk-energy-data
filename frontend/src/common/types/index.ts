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

/**
 * One settlement period's day-ahead price — the volume weighted average
 * across market index data providers (APX/N2EX), the closest free proxy for
 * GB's day-ahead auction clearing price. `settlementPeriod` is null once
 * resampled to a daily/weekly mean over wider ranges, same as
 * `ImbalancePricePoint`.
 */
export interface DayAheadPricePoint {
  timestamp: string
  settlementPeriod: number | null
  price: number
}

/**
 * Average day-ahead price for one settlement period (1-48), aggregated
 * across a whole date range — the typical daily price shape a VPP schedules
 * its charge/discharge cycle around.
 */
export interface DayAheadPriceProfilePoint {
  settlementPeriod: number
  meanPrice: number
  stdPrice: number
  sampleCount: number
}

/** One settlement period's predicted day-ahead price band. */
export interface QuantilePricePoint {
  settlementPeriod: number
  p10: number
  p50: number
  p90: number
}

/**
 * Tomorrow's predicted day-ahead price, as a quantile band per settlement
 * period. `points` may have fewer than the expected number of periods if
 * some don't yet have enough price history to build their features.
 */
export interface DayAheadForecastResponse {
  forecastDate: string
  generatedAt: string
  quantiles: number[]
  points: QuantilePricePoint[]
}

export interface ModelFeatureDescription {
  name: string
  description: string
}

/** Describes how the currently-cached forecasting model was built. */
export interface ModelInfoResponse {
  algorithm: string
  quantiles: number[]
  features: ModelFeatureDescription[]
  trainingWindowStart: string
  trainingWindowEnd: string
  trainingRowCount: number
  trainedAt: string
  hyperparameters: Record<string, number>
}

export interface QuantileBacktestMetric {
  quantile: number
  pinballLoss: number
  nominalCoverage: number
  empiricalCoverage: number
}

/**
 * Out-of-sample model quality on a holdout window, per quantile, plus a
 * head-to-head comparison against the naive persistence baseline (last
 * week's price) at the median.
 */
export interface BacktestResponse {
  holdoutStart: string
  holdoutEnd: string
  holdoutRowCount: number
  quantileMetrics: QuantileBacktestMetric[]
  persistenceBaselinePinballLossP50: number
  modelPinballLossP50: number
}
