import { useEffect, useState } from 'react'
import { apiGet } from '../api/client'

/** Grid data updates roughly every settlement period; poll well within that window. */
const DEFAULT_REFRESH_INTERVAL_MS = 2 * 60 * 1000

interface ApiDataState<T> {
  data: T | null
  error: Error | null
  isLoading: boolean
}

/**
 * Fetches `path` from the backend on mount and, if `refreshIntervalMs` is
 * positive, on a fixed interval after that — so dashboard charts stay
 * current with live grid data. Pass `0` to fetch once only, for a historical
 * range that won't change. Errors are captured rather than thrown, so a
 * single flaky request just leaves the last good data on screen rather than
 * crashing the page.
 */
export function useApiData<T>(
  path: string,
  refreshIntervalMs: number = DEFAULT_REFRESH_INTERVAL_MS,
): ApiDataState<T> {
  const [state, setState] = useState<ApiDataState<T>>({
    data: null,
    error: null,
    isLoading: true,
  })

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const data = await apiGet<T>(path)
        if (!cancelled) setState({ data, error: null, isLoading: false })
      } catch (error) {
        if (!cancelled) {
          setState((prev) => ({
            data: prev.data,
            error: error as Error,
            isLoading: false,
          }))
        }
      }
    }

    load()
    const intervalId = refreshIntervalMs > 0 ? setInterval(load, refreshIntervalMs) : undefined

    return () => {
      cancelled = true
      if (intervalId) clearInterval(intervalId)
    }
  }, [path, refreshIntervalMs])

  return state
}
