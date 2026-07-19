import { NavLink } from 'react-router-dom'

const TABS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/forecasting', label: 'Forecasting' },
  { to: '/vpp', label: 'VPP Optimisation' },
]

export function NavBar() {
  return (
    <nav className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
        <span className="font-semibold text-slate-900 dark:text-slate-100">
          UK Energy Grid Data & VPP Optimisation
        </span>
        <div className="flex gap-4">
          {TABS.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              className={({ isActive }) =>
                `rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-brand text-white'
                    : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
                }`
              }
            >
              {tab.label}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  )
}
