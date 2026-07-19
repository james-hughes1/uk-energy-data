/** A single (timestamp, value) sample, the common shape for time-series data across pages. */
export interface TimeSeriesPoint {
  timestamp: string
  value: number
}
