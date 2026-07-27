import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { App } from '../src/App'

// Plotly renders to a real <canvas>, which jsdom can't back — stub it out
// so this smoke test can exercise routing/layout without a browser.
vi.mock('react-plotly.js', () => ({
  default: () => <div data-testid="plot-stub" />,
}))

// The dashboard page fetches live grid data on mount — stub it out so this
// smoke test only exercises routing/layout, not the network.
beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => Promise.resolve(new Response(JSON.stringify([])))),
  )
})

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('App', () => {
  it('renders the nav tabs for every subproject', () => {
    renderAt('/dashboard')

    expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Forecasting' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'VPP Optimisation' })).toBeInTheDocument()
  })

  it('redirects the default route to the dashboard page', () => {
    renderAt('/')

    expect(screen.getByRole('heading', { name: 'Live grid dashboard' })).toBeInTheDocument()
  })

  it('renders the forecasting page at /forecasting', () => {
    renderAt('/forecasting')

    expect(screen.getByRole('heading', { name: 'Price forecasting' })).toBeInTheDocument()
  })

  it('renders the VPP page at /vpp', () => {
    renderAt('/vpp')

    expect(screen.getByRole('heading', { name: 'VPP optimisation' })).toBeInTheDocument()
  })
})
