/**
 * Must stay in sync with `backend/app/services/elexon_client.py`'s
 * `EARLIEST_AVAILABLE_DATE` and `IMBALANCE_PRICE_MAX_DAYS` constants.
 */
export const EARLIEST_AVAILABLE_DATE = '2016-03-01'
export const IMBALANCE_PRICE_MAX_DAYS = 90

export const DATE_RANGE_PRESETS = [
  { key: 'last24h', label: 'Last 24 hours' },
  { key: 'last7d', label: 'Last 7 days' },
  { key: 'last30d', label: 'Last 30 days' },
  { key: 'last1y', label: 'Last year' },
  { key: 'allTime', label: 'All time (since Mar 2016)' },
] as const

export type PresetKey = (typeof DATE_RANGE_PRESETS)[number]['key']

export type DateRangeSelection =
  { type: 'preset'; key: PresetKey } | { type: 'custom'; start: string; end: string }

export interface ResolvedDateRange {
  start: string
  end: string
  /** True only for the rolling "last 24 hours" view, where charts should keep polling. */
  isLive: boolean
}

function toIsoDate(date: Date): string {
  return date.toISOString().slice(0, 10)
}

function resolvePreset(key: PresetKey): { start: string; end: string } {
  const end = new Date()
  if (key === 'allTime') return { start: EARLIEST_AVAILABLE_DATE, end: toIsoDate(end) }

  const start = new Date(end)
  switch (key) {
    case 'last24h':
      start.setDate(start.getDate() - 1)
      break
    case 'last7d':
      start.setDate(start.getDate() - 7)
      break
    case 'last30d':
      start.setDate(start.getDate() - 30)
      break
    case 'last1y':
      start.setFullYear(start.getFullYear() - 1)
      break
  }
  return { start: toIsoDate(start), end: toIsoDate(end) }
}

export function resolveDateRangeSelection(selection: DateRangeSelection): ResolvedDateRange {
  if (selection.type === 'preset') {
    return { ...resolvePreset(selection.key), isLive: selection.key === 'last24h' }
  }
  return { start: selection.start, end: selection.end, isLive: false }
}

export function describeSelection(selection: DateRangeSelection): string {
  if (selection.type === 'preset') {
    return (
      DATE_RANGE_PRESETS.find((preset) => preset.key === selection.key)?.label ?? 'Custom range'
    )
  }
  return `${selection.start} → ${selection.end}`
}
