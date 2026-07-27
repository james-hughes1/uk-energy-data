import type { ReactNode } from 'react'

interface ChartCardProps {
  title: string
  /** True only while there's no data to show yet (first load). */
  isLoading: boolean
  /** Set once data has been fetched at least once, even if a later refresh fails. */
  hasData: boolean
  error: Error | null
  children: ReactNode
}

/**
 * Shared chart chrome: title + bordered card, with loading/error states
 * handled once so individual charts only need to render their plot.
 * A failed refresh keeps the previous chart on screen (with a small notice)
 * rather than flashing empty; only a failure with no prior data blocks render.
 */
export function ChartCard({ title, isLoading, hasData, error, children }: ChartCardProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">{title}</h2>
        {error && hasData && (
          <span className="text-xs text-red-600 dark:text-red-400">
            Couldn&apos;t refresh — showing last known data
          </span>
        )}
      </div>
      {isLoading && (
        <div className="flex h-80 items-center justify-center text-sm text-slate-400 dark:text-slate-500">
          Loading…
        </div>
      )}
      {!isLoading && !hasData && error && (
        <div className="flex h-80 items-center justify-center text-sm text-red-600 dark:text-red-400">
          Couldn&apos;t load data from the backend.
        </div>
      )}
      {hasData && children}
    </div>
  )
}
