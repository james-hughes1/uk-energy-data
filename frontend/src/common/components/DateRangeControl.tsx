import { useEffect, useRef, useState } from 'react'
import {
  DATE_RANGE_PRESETS,
  EARLIEST_AVAILABLE_DATE,
  describeSelection,
  type DateRangeSelection,
} from '../utils/dateRange'

const TODAY = new Date().toISOString().slice(0, 10)

interface DateRangeControlProps {
  selection: DateRangeSelection
  onChange: (selection: DateRangeSelection) => void
}

/**
 * Shared date-range filter for the whole dashboard — one control above all
 * the charts, so every chart re-renders against the same slice of time.
 * Presets are listed as rows (per the project's data-viz conventions), with
 * a custom range tucked below a hairline divider.
 */
export function DateRangeControl({ selection, onChange }: DateRangeControlProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [customStart, setCustomStart] = useState(selection.type === 'custom' ? selection.start : '')
  const [customEnd, setCustomEnd] = useState(selection.type === 'custom' ? selection.end : '')
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function selectPreset(key: (typeof DATE_RANGE_PRESETS)[number]['key']) {
    onChange({ type: 'preset', key })
    setIsOpen(false)
  }

  function applyCustomRange() {
    if (!customStart || !customEnd) return
    onChange({ type: 'custom', start: customStart, end: customEnd })
    setIsOpen(false)
  }

  return (
    <div ref={containerRef} className="relative flex justify-start">
      <button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
        aria-expanded={isOpen}
      >
        {describeSelection(selection)} <span aria-hidden="true">▾</span>
      </button>

      {isOpen && (
        <div className="absolute top-full z-10 mt-1 w-64 rounded-lg border border-slate-200 bg-white p-1 shadow-lg dark:border-slate-800 dark:bg-slate-900">
          {DATE_RANGE_PRESETS.map((preset) => {
            const isSelected = selection.type === 'preset' && selection.key === preset.key
            return (
              <button
                key={preset.key}
                type="button"
                onClick={() => selectPreset(preset.key)}
                className="flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                {preset.label}
                {isSelected && <span aria-hidden="true">✓</span>}
              </button>
            )
          })}

          <div className="mt-1 border-t border-slate-200 p-3 dark:border-slate-800">
            <p className="mb-2 text-xs font-medium text-slate-500 dark:text-slate-400">
              Custom range
            </p>
            <div className="flex items-center gap-2">
              <input
                type="date"
                value={customStart}
                onChange={(e) => setCustomStart(e.target.value)}
                min={EARLIEST_AVAILABLE_DATE}
                max={TODAY}
                className="w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
              />
              <span className="text-slate-400">–</span>
              <input
                type="date"
                value={customEnd}
                onChange={(e) => setCustomEnd(e.target.value)}
                min={EARLIEST_AVAILABLE_DATE}
                max={TODAY}
                className="w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
              />
            </div>
            <button
              type="button"
              onClick={applyCustomRange}
              disabled={!customStart || !customEnd}
              className="mt-2 w-full rounded-md bg-brand px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-50"
            >
              Apply
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
