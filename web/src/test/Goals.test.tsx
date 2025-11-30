import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Goals from '../components/Goals'
import { api } from '../services/api'

vi.mock('../services/api')

describe('Goals Component', () => {
  const mockGoals = {
    goals: [
      {
        id: '1',
        name: 'Emergency Fund',
        target_amount: 10000,
        current_amount: 5000,
        target_date: '2026-12-31',
        status: 'active',
        progress_percentage: 50,
      },
      {
        id: '2',
        name: 'Vacation',
        target_amount: 5000,
        current_amount: 1000,
        target_date: '2026-06-01',
        status: 'active',
        progress_percentage: 20,
      },
    ],
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders goals list', async () => {
    vi.mocked(api.getGoals).mockResolvedValue(mockGoals)
    
    render(<Goals />)
    
    await waitFor(() => {
      expect(screen.getByText('Emergency Fund')).toBeInTheDocument()
      expect(screen.getByText('Vacation')).toBeInTheDocument()
    })
  })

  it('displays progress percentage', async () => {
    vi.mocked(api.getGoals).mockResolvedValue(mockGoals)
    
    render(<Goals />)
    
    await waitFor(() => {
      expect(screen.getByText('50.0%')).toBeInTheDocument()
      expect(screen.getByText('20.0%')).toBeInTheDocument()
    })
  })

  it('shows add goal form when button clicked', async () => {
    vi.mocked(api.getGoals).mockResolvedValue({ goals: [] })
    const user = userEvent.setup()
    
    render(<Goals />)
    
    await waitFor(() => screen.getByRole('button', { name: /add goal/i }))
    
    const addBtn = screen.getByRole('button', { name: /add goal/i })
    await user.click(addBtn)
    
    expect(screen.getByPlaceholderText(/goal name/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/target amount/i)).toBeInTheDocument()
  })

  it('adds new goal', async () => {
    vi.mocked(api.getGoals).mockResolvedValue({ goals: [] })
    vi.mocked(api.addGoal).mockResolvedValue({ success: true })
    const user = userEvent.setup()
    
    render(<Goals />)
    
    await waitFor(() => screen.getByRole('button', { name: /add goal/i }))
    
    const addBtn = screen.getByRole('button', { name: /add goal/i })
    await user.click(addBtn)
    
    await user.type(screen.getByPlaceholderText(/goal name/i), 'New Car')
    await user.type(screen.getByPlaceholderText(/target amount/i), '30000')
    await user.type(screen.getByPlaceholderText(/current amount/i), '5000')
    
    const dateInput = screen.getByDisplayValue('')
    await user.type(dateInput, '2027-12-31')
    
    const submitBtn = screen.getByRole('button', { name: /add goal/i })
    await user.click(submitBtn)
    
    await waitFor(() => {
      expect(api.addGoal).toHaveBeenCalledWith({
        name: 'New Car',
        target_amount: 30000,
        current_amount: 5000,
        target_date: '2027-12-31',
      })
    })
  })

  it('updates goal progress', async () => {
    vi.mocked(api.getGoals).mockResolvedValue(mockGoals)
    vi.mocked(api.updateGoalProgress).mockResolvedValue({ success: true })
    global.prompt = vi.fn(() => '500')
    const user = userEvent.setup()
    
    render(<Goals />)
    
    await waitFor(() => screen.getByText('Emergency Fund'))
    
    const progressButtons = screen.getAllByRole('button', { name: /add progress/i })
    await user.click(progressButtons[0])
    
    expect(global.prompt).toHaveBeenCalled()
    expect(api.updateGoalProgress).toHaveBeenCalledWith('1', 500)
  })

  it('shows empty state when no goals', async () => {
    vi.mocked(api.getGoals).mockResolvedValue({ goals: [] })
    
    render(<Goals />)
    
    await waitFor(() => {
      expect(screen.getByText(/no goals yet/i)).toBeInTheDocument()
    })
  })
})
