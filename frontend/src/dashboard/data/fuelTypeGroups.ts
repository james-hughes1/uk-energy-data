/**
 * Elexon reports 11 individual PSR (fuel) types, more than a stacked area
 * chart can carry as distinct hues (see the data-viz categorical palette:
 * max 8 slots for adjacent-pair colour-vision-deficiency safety). Onshore
 * and offshore wind are grouped into one "Wind" band to make room for coal
 * to have its own line — coal looks marginal in any *recent* window, but was
 * a major fuel source earlier in this dashboard's history (~3,000 MW in
 * 2016), and its decline to near-zero is one of the more telling stories in
 * the "all time" view, so it shouldn't be buried in "Other". Oil and
 * Elexon's own "Other" catch-all are genuinely marginal throughout, so they
 * share a single "Other" band; the two hydro PSR types are grouped into one
 * "Hydro" band. This keeps the chart at a fixed 8 categories, each with a
 * colour that never changes with the data.
 */
const FUEL_TYPE_GROUPS: Record<string, string> = {
  'Fossil Gas': 'Gas',
  'Fossil Hard coal': 'Coal',
  Nuclear: 'Nuclear',
  'Wind Onshore': 'Wind',
  'Wind Offshore': 'Wind',
  Solar: 'Solar',
  'Hydro Pumped Storage': 'Hydro',
  'Hydro Run-of-river and poundage': 'Hydro',
  Biomass: 'Biomass',
  'Fossil Oil': 'Other',
  Other: 'Other',
}

/** Fixed stacking order, matched 1:1 with the fixed categorical colour slots. */
export const FUEL_TYPE_GROUP_ORDER = [
  'Wind',
  'Biomass',
  'Hydro',
  'Solar',
  'Coal',
  'Gas',
  'Nuclear',
  'Other',
] as const

export function groupFuelType(psrType: string): string {
  return FUEL_TYPE_GROUPS[psrType] ?? 'Other'
}
