import type { ReactNode } from 'react'

interface PageLayoutProps {
  title: string
  description: string
  children: ReactNode
}

/** Shared page chrome (heading + intro) used by every subproject page. */
export function PageLayout({ title, description, children }: PageLayoutProps) {
  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{title}</h1>
      <p className="mt-1 max-w-2xl text-slate-600 dark:text-slate-400">{description}</p>
      <div className="mt-6 flex flex-col gap-6">{children}</div>
    </main>
  )
}
