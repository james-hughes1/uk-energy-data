import { useEffect, useState } from 'react'

/**
 * Fixed categorical palette (8 slots), validated for colour-vision-deficiency
 * safety in adjacent-pair use (stacked areas, grouped lines) in both light and
 * dark mode. Colour is assigned per entity below and never reassigned by rank,
 * so a series keeps its colour across refetches even if its magnitude changes.
 */
const CATEGORICAL_LIGHT = [
  '#2a78d6', // 1 blue
  '#008300', // 2 green
  '#e87ba4', // 3 magenta
  '#eda100', // 4 yellow
  '#1baf7a', // 5 aqua
  '#eb6834', // 6 orange
  '#4a3aa7', // 7 violet
  '#e34948', // 8 red
] as const

const CATEGORICAL_DARK = [
  '#3987e5', // 1 blue
  '#008300', // 2 green
  '#d55181', // 3 magenta
  '#c98500', // 4 yellow
  '#199e70', // 5 aqua
  '#d95926', // 6 orange
  '#9085e9', // 7 violet
  '#e66767', // 8 red
] as const

export const CHART_SLOT = {
  blue: 0,
  green: 1,
  magenta: 2,
  yellow: 3,
  aqua: 4,
  orange: 5,
  violet: 6,
  red: 7,
} as const

/** Tracks the `prefers-color-scheme` media query, matching the app's dark-mode strategy. */
export function usePrefersDarkMode(): boolean {
  const [prefersDark, setPrefersDark] = useState(
    () => window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false,
  )

  useEffect(() => {
    const query = window.matchMedia('(prefers-color-scheme: dark)')
    const listener = (event: MediaQueryListEvent) => setPrefersDark(event.matches)
    query.addEventListener('change', listener)
    return () => query.removeEventListener('change', listener)
  }, [])

  return prefersDark
}

/** Looks up a fixed categorical slot's colour for the current colour scheme. */
export function useCategoricalColor(slot: number): string {
  const prefersDark = usePrefersDarkMode()
  return (prefersDark ? CATEGORICAL_DARK : CATEGORICAL_LIGHT)[slot]
}

export function useCategoricalColors(slots: number[]): string[] {
  const prefersDark = usePrefersDarkMode()
  const palette = prefersDark ? CATEGORICAL_DARK : CATEGORICAL_LIGHT
  return slots.map((slot) => palette[slot])
}
