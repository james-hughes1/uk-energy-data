import { useState, type ReactNode } from 'react'

interface ExplainerPanelProps {
  title: string
  children: ReactNode
}

/**
 * Collapsible "what does this mean?" box. Every page uses this to hold the
 * real-world/ML context explanations called for by the project guidelines,
 * so explanatory content has one consistent home across subprojects.
 */
export function ExplainerPanel({ title, children }: ExplainerPanelProps) {
  const [open, setOpen] = useState(true)

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between text-left font-medium text-slate-900 dark:text-slate-100"
        aria-expanded={open}
      >
        {title}
        <span aria-hidden="true">{open ? '−' : '+'}</span>
      </button>
      {open && <div className="mt-3 text-sm text-slate-600 dark:text-slate-400">{children}</div>}
    </section>
  )
}
