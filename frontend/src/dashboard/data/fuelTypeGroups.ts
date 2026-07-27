/**
 * Elexon reports 11 individual PSR (fuel) types, more than a stacked area
 * chart can carry as distinct hues (see the data-viz categorical palette:
 * max 8 slots for adjacent-pair colour-vision-deficiency safety). Coal, oil,
 * and Elexon's own "Other" catch-all are all marginal contributors to the GB
 * mix today, so they're grouped into a single "Other" band; the two hydro
 * PSR types are grouped into one "Hydro" band. This keeps the chart at a
 * fixed 8 categories, each with a colour that never changes with the data.
 */
const FUEL_TYPE_GROUPS: Record<string, string> = {
  'Fossil Gas': 'Gas',
  Nuclear: 'Nuclear',
  'Wind Onshore': 'Wind onshore',
  'Wind Offshore': 'Wind offshore',
  Solar: 'Solar',
  'Hydro Pumped Storage': 'Hydro',
  'Hydro Run-of-river and poundage': 'Hydro',
  Biomass: 'Biomass',
  'Fossil Hard coal': 'Other',
  'Fossil Oil': 'Other',
  Other: 'Other',
}

/** Fixed stacking order, matched 1:1 with the fixed categorical colour slots. */
export const FUEL_TYPE_GROUP_ORDER = [
  'Wind onshore',
  'Biomass',
  'Hydro',
  'Solar',
  'Wind offshore',
  'Gas',
  'Nuclear',
  'Other',
] as const

export function groupFuelType(psrType: string): string {
  return FUEL_TYPE_GROUPS[psrType] ?? 'Other'
}
