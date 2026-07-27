import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { DateRangeControl } from '../src/common/components/DateRangeControl'
import type { DateRangeSelection } from '../src/common/utils/dateRange'

describe('DateRangeControl', () => {
  it('shows the current preset label on the trigger button', () => {
    render(<DateRangeControl selection={{ type: 'preset', key: 'last7d' }} onChange={vi.fn()} />)

    expect(screen.getByRole('button', { name: /Last 7 days/ })).toBeInTheDocument()
  })

  it('lists every preset once opened', async () => {
    const user = userEvent.setup()
    render(<DateRangeControl selection={{ type: 'preset', key: 'last24h' }} onChange={vi.fn()} />)

    await user.click(screen.getByRole('button', { name: /Last 24 hours/ }))

    for (const label of ['Last 7 days', 'Last 30 days', 'Last year', /All time/]) {
      expect(screen.getByRole('button', { name: label })).toBeInTheDocument()
    }
  })

  it('calls onChange with the selected preset and closes the dropdown', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<DateRangeControl selection={{ type: 'preset', key: 'last24h' }} onChange={onChange} />)

    await user.click(screen.getByRole('button', { name: /Last 24 hours/ }))
    await user.click(screen.getByRole('button', { name: 'Last 30 days' }))

    expect(onChange).toHaveBeenCalledWith({ type: 'preset', key: 'last30d' })
    expect(screen.queryByRole('button', { name: 'Last 7 days' })).not.toBeInTheDocument()
  })

  it('applies a custom range once both dates are filled in', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<DateRangeControl selection={{ type: 'preset', key: 'last24h' }} onChange={onChange} />)

    await user.click(screen.getByRole('button', { name: /Last 24 hours/ }))
    const applyButton = screen.getByRole('button', { name: 'Apply' })
    expect(applyButton).toBeDisabled()

    const [startInput, endInput] = screen.getAllByDisplayValue('') as HTMLInputElement[]
    await user.type(startInput, '2020-01-01')
    await user.type(endInput, '2020-02-01')

    expect(applyButton).toBeEnabled()
    await user.click(applyButton)

    const expected: DateRangeSelection = { type: 'custom', start: '2020-01-01', end: '2020-02-01' }
    expect(onChange).toHaveBeenCalledWith(expected)
  })
})
