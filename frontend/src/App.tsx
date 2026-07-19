import { Navigate, Route, Routes } from 'react-router-dom'
import { NavBar } from './common/components/NavBar'
import { ErrorBoundary } from './common/components/ErrorBoundary'
import { DashboardPage } from './dashboard/DashboardPage'
import { ForecastingPage } from './forecasting/ForecastingPage'
import { VppPage } from './vpp/VppPage'

// Route table only — the router itself is owned by main.tsx so this
// component can be rendered under a MemoryRouter in tests.
export function App() {
  return (
    <div className="min-h-screen">
      <NavBar />
      <ErrorBoundary>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/forecasting" element={<ForecastingPage />} />
          <Route path="/vpp" element={<VppPage />} />
        </Routes>
      </ErrorBoundary>
    </div>
  )
}
