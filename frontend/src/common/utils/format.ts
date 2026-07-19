/** Formats a price in £/MWh with a fixed 2 decimal places, e.g. "£54.32/MWh". */
export function formatPrice(value: number): string {
  return `£${value.toFixed(2)}/MWh`
}

/** Formats an ISO timestamp as a short local time, e.g. "14:05". */
export function formatTime(isoTimestamp: string): string {
  return new Date(isoTimestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })
}
