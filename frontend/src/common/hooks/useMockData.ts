import { useMemo } from 'react'
import type { TimeSeriesPoint } from '../types'

/**
 * Generates deterministic placeholder time-series data so pages have
 * something to render before they're wired up to the real backend.
 */
export function useMockData(
  points: number,
  baseValue: number,
  amplitude: number,
): TimeSeriesPoint[] {
  return useMemo(() => {
    const now = Date.now()
    return Array.from({ length: points }, (_, i) => ({
      timestamp: new Date(now - (points - i) * 30 * 60 * 1000).toISOString(),
      value: baseValue + amplitude * Math.sin(i / 3) + (i % 5) * 0.5,
    }))
  }, [points, baseValue, amplitude])
}
