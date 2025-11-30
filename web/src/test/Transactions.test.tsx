import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Transactions from '../components/Transactions'
import { api } from '../services/api'

vi.mock('../services/api')

describe('Transactions Component', () => {
  const mockTransactions = {
    transactions: [
      {
        id: '1',
        type: 'expense' as const,
        amount: 45.50,
        description: 'Groceries at Whole Foods',
        category: 'groceries',
        date: '2025-11-06T10:00:00Z',
      },
      {
        id: '2',
        type: 'income' as const,
        amount: 5000,
        description: 'Monthly salary',
        category: 'salary',
        date: '2025-11-01T10:00:00Z',
      },
    ],
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders transactions list', async () => {
    vi.mocked(api.getTransactions).mockResolvedValue(mockTransactions)
    
    render(<Transactions />)
    
    await waitFor(() => {
      expect(screen.getByText('Groceries at Whole Foods')).toBeInTheDocument()
      expect(screen.getByText('Monthly salary')).toBeInTheDocument()
    })
  })

  it('shows add transaction form when button clicked', async () => {
    vi.mocked(api.getTransactions).mockResolvedValue({ transactions: [] })
    const user = userEvent.setup()
    
    render(<Transactions />)
    
    await waitFor(() => screen.getByRole('button', { name: /add transaction/i }))
    
    const addBtn = screen.getByRole('button', { name: /add transaction/i })
    await user.click(addBtn)
    
    expect(screen.getByPlaceholderText(/amount/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/category/i)).toBeInTheDocument()
  })

  it('adds new transaction', async () => {
    vi.mocked(api.getTransactions).mockResolvedValue({ transactions: [] })
    vi.mocked(api.addTransaction).mockResolvedValue({ success: true })
    const user = userEvent.setup()
    
    render(<Transactions />)
    
    await waitFor(() => screen.getByRole('button', { name: /add transaction/i }))
    
    const addBtn = screen.getByRole('button', { name: /add transaction/i })
    await user.click(addBtn)
    
    await user.type(screen.getByPlaceholderText(/amount/i), '100')
    await user.type(screen.getByPlaceholderText(/category/i), 'food')
    await user.type(screen.getByPlaceholderText(/description/i), 'Lunch')
    
    const submitBtn = screen.getByRole('button', { name: /add transaction/i })
    await user.click(submitBtn)
    
    await waitFor(() => {
      expect(api.addTransaction).toHaveBeenCalledWith({
        type: 'expense',
        amount: 100,
        category: 'food',
        description: 'Lunch',
      })
    })
  })

  it('deletes transaction with confirmation', async () => {
    vi.mocked(api.getTransactions).mockResolvedValue(mockTransactions)
    vi.mocked(api.deleteTransaction).mockResolvedValue({ success: true })
    global.confirm = vi.fn(() => true)
    const user = userEvent.setup()
    
    render(<Transactions />)
    
    await waitFor(() => screen.getByText('Groceries at Whole Foods'))
    
    const deleteButtons = screen.getAllByRole('button', { name: /🗑️/i })
    await user.click(deleteButtons[0])
    
    expect(global.confirm).toHaveBeenCalled()
    expect(api.deleteTransaction).toHaveBeenCalledWith('1')
  })

  it('shows empty state when no transactions', async () => {
    vi.mocked(api.getTransactions).mockResolvedValue({ transactions: [] })
    
    render(<Transactions />)
    
    await waitFor(() => {
      expect(screen.getByText(/no transactions yet/i)).toBeInTheDocument()
    })
  })
})
