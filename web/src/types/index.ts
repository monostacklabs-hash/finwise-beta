// Type definitions for FinWise AI Web App

export interface User {
  id: string
  email: string
  name: string
  currency?: string
  timezone?: string
  country?: string
}

export interface Transaction {
  id: string
  type: 'income' | 'expense'
  amount: number
  description: string
  category: string
  date: string
  account_id?: string
}

export interface Goal {
  id: string
  name: string
  target_amount: number
  current_amount: number
  target_date: string
  status: string
  progress_percentage: number
}

export interface Debt {
  id: string
  type: string
  name: string
  remaining_amount: number
  interest_rate: number
  monthly_payment: number
  status: string
}

export interface Account {
  id: string
  account_type: string
  account_name: string
  institution_name?: string
  account_number_last4?: string
  current_balance: number
  currency: string
  status: string
  credit_card?: CreditCard
}

export interface CreditCard {
  id: string
  credit_limit: number
  available_credit: number
  apr?: number
  statement_balance: number
  minimum_payment: number
  payment_due_date?: string
  credit_utilization: number
}

export interface Budget {
  id: string
  category: string
  amount: number
  spent: number
  remaining: number
  period: string
  percentage_used: number
  status: 'on_track' | 'warning' | 'exceeded'
}

export interface RecurringTransaction {
  id: string
  type: 'income' | 'expense'
  amount: number
  description: string
  category: string
  frequency: 'daily' | 'weekly' | 'monthly' | 'yearly'
  next_date: string
  auto_add: boolean
  remind_days_before: number
}

export interface Notification {
  id: string
  type: string
  title: string
  message: string
  status: 'unread' | 'read'
  priority: number
  action_url?: string
  created_at: string
}

export interface FinancialHealth {
  health_score: number
  assessment: string
  net_worth: number
  total_income: number
  total_expenses: number
  total_debt: number
  savings_rate: number
  debt_to_income_ratio: number
  liquidity_ratio: number
  recommendations: string[]
}

export interface CashFlowForecast {
  forecast: Array<{
    date: string
    balance: number
    income: number
    expenses: number
  }>
  summary: {
    starting_balance: number
    ending_balance: number
    total_income: number
    total_expenses: number
  }
}
