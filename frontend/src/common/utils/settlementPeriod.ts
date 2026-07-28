/** Settlement period 1 covers 00:00-00:30, period 2 covers 00:30-01:00, and so on. */
export function periodToTimeLabel(settlementPeriod: number): string {
  const minutesFromMidnight = (settlementPeriod - 1) * 30
  const hours = Math.floor(minutesFromMidnight / 60) % 24
  const minutes = minutesFromMidnight % 60
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`
}
