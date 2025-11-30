import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Dashboard from '../components/Dashboard'
import { api } from '../services/api'

vi.mock('../services/api')

describe('Dashboard Component', () => {
  const mockHealth = {
    health_score: 85,
    assessment: 'Excellent financial health!',
    net_worth: 50000,
    total_income: 100000,
    total_expenses: 40000,
    total_debt: 10000,
    savings_rate: 0.6,
    debt_to_income_ratio: 0.1,
    liquidity_ratio: 5.0,
    recommendations: [
      'Keep up the great work!',
      'Consider investing more',
    ],
  }

  const mockNavigate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    vi.mocked(api.getFinancialHealth).mockImplementation(() => new Promise(() => {}))
    render(<Dashboard onNavigate={mockNavigate} />)
    expect(screen.getByText(/loading dashboard/i)).toBeInTheDocument()
  })

  it('renders financial health data', async () => {
    vi.mocked(api.getFinancialHealth).mockResolvedValue(mockHealth)
    
    render(<Dashboard onNavigate={mockNavigate} />)
    
    await waitFor(() => {
      expect(screen.getByText('85')).toBeInTheDocument()
      expect(screen.getByText('Excellent financial health!')).toBeInTheDocument()
      expect(screen.getByText(/\$50,000/)).toBeInTheDocument()
    })
  })

  it('displays recommendations', async () => {
    vi.mocked(api.getFinancialHealth).mockResolvedValue(mockHealth)
    
    render(<Dashboard onNavigate={mockNavigate} />)
    
    await waitFor(() => {
      expect(screen.getByText('Keep up the great work!')).toBeInTheDocument()
      expect(screen.getByText('Consider investing more')).toBeInTheDocument()
    })
  })

  it('navigates to transactions when button clicked', async () => {
    vi.mocked(api.getFinancialHealth).mockResolvedValue(mockHealth)
    const user = userEvent.setup()
    
    render(<Dashboard onNavigate={mockNavigate} />)
    
    await waitFor(() => screen.getByText(/transactions/i))
    
    const transactionsBtn = screen.getByRole('button', { name: /transactions/i })
    await user.click(transactionsBtn)
    
    expect(mockNavigate).toHaveBeenCalledWith('transactions')
  })

  it('handles error state', async () => {
    vi.mocked(api.getFinancialHealth).mockRejectedValue(new Error('API Error'))
    
    render(<Dashboard onNavigate={mockNavigate} />)
    
    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument()
    })
  })

  it('refreshes data when refresh button clicked', async () => {
    vi.mocked(api.getFinancialHealth).mockResolvedValue(mockHealth)
    const user = userEvent.setup()
    
    render(<Dashboard onNavigate={mockNavigate} />)
    
    await waitFor(() => screen.getByText('85'))
    
    const refreshBtn = screen.getByRole('button', { name: /refresh/i })
    await user.click(refreshBtn)
    
    expect(api.getFinancialHealth).toHaveBeenCalledTimes(2)
  })
})
