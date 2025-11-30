// API service for FinWise AI Web App
import axios, { AxiosInstance } from 'axios'
import type {
  User,
  Transaction,
  Goal,
  Debt,
  Account,
  Budget,
  RecurringTransaction,
  Notification,
  FinancialHealth,
  CashFlowForecast,
} from '../types'

class ApiService {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: '/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })
  }

  // Auth
  async login(email: string, password: string) {
    const { data } = await this.client.post('/auth/login', { email, password })
    return data
  }

  async register(email: string, password: string, name: string) {
    const { data } = await this.client.post('/auth/register', { email, password, name })
    return data
  }

  async getProfile(): Promise<User> {
    const { data } = await this.client.get('/auth/profile')
    return data
  }

  // Chat
  async chat(message: string, chatHistory?: any[]) {
    const { data } = await this.client.post('/chat', { message, chat_history: chatHistory })
    return data
  }

  // Dashboard
  async getDashboard() {
    const { data } = await this.client.get('/dashboard')
    return data
  }

  async getFinancialHealth(): Promise<FinancialHealth> {
    const { data } = await this.client.get('/financial-health')
    return data
  }

  // Transactions
  async getTransactions(limit = 50): Promise<{ transactions: Transaction[] }> {
    const { data } = await this.client.get(`/transactions?limit=${limit}`)
    return data
  }

  async addTransaction(transaction: {
    type: string
    amount: number
    category: string
    description: string
  }) {
    const { data } = await this.client.post('/transactions', transaction)
    return data
  }

  async deleteTransaction(id: string) {
    const { data } = await this.client.delete(`/transactions/${id}`)
    return data
  }

  // Goals
  async getGoals(): Promise<{ goals: Goal[] }> {
    const { data } = await this.client.get('/goals')
    return data
  }

  async addGoal(goal: {
    name: string
    target_amount: number
    target_date: string
    current_amount?: number
  }) {
    const { data } = await this.client.post('/goals', goal)
    return data
  }

  async updateGoalProgress(id: string, amount: number) {
    const { data } = await this.client.put(`/goals/${id}/progress`, null, { params: { amount } })
    return data
  }

  async deleteGoal(id: string) {
    const { data } = await this.client.delete(`/goals/${id}`)
    return data
  }

  // Debts
  async getDebts(): Promise<{ debts: Debt[] }> {
    const { data } = await this.client.get('/debts')
    return data
  }

  async addDebt(debt: {
    type: string
    name: string
    remaining_amount: number
    interest_rate: number
    monthly_payment: number
  }) {
    const { data } = await this.client.post('/debts', debt)
    return data
  }

  async makeDebtPayment(id: string, amount: number) {
    const { data } = await this.client.post(`/debts/${id}/payment`, null, { params: { amount } })
    return data
  }

  async deleteDebt(id: string) {
    const { data } = await this.client.delete(`/debts/${id}`)
    return data
  }

  // Accounts
  async getAccounts(): Promise<{ accounts: Account[] }> {
    const { data } = await this.client.get('/accounts')
    return data
  }

  async addAccount(account: {
    account_type: string
    account_name: string
    institution_name?: string
    account_number_last4?: string
    current_balance: number
    currency?: string
    opening_date?: string
    interest_rate?: number
    notes?: string
  }) {
    const { data } = await this.client.post('/accounts', account)
    return data
  }

  async updateAccount(id: string, updates: any) {
    const { data } = await this.client.put(`/accounts/${id}`, updates)
    return data
  }

  async deleteAccount(id: string) {
    const { data } = await this.client.delete(`/accounts/${id}`)
    return data
  }

  // Budgets
  async getBudgets(): Promise<{ budgets: Budget[] }> {
    const { data } = await this.client.get('/budgets')
    return data
  }

  async createBudget(budget: {
    category: string
    amount: number
    period: string
    start_date?: string
    alert_threshold?: number
  }) {
    const { data } = await this.client.post('/budgets', budget)
    return data
  }

  async updateBudget(id: string, updates: any) {
    const { data } = await this.client.put(`/budgets/${id}`, updates)
    return data
  }

  async deleteBudget(id: string) {
    const { data } = await this.client.delete(`/budgets/${id}`)
    return data
  }

  // Recurring Transactions
  async getRecurringTransactions(): Promise<{ recurring_transactions: RecurringTransaction[] }> {
    const { data } = await this.client.get('/recurring-transactions')
    return data
  }

  async getRecurringSuggestions() {
    const { data } = await this.client.get('/recurring-transactions/suggestions')
    return data
  }

  async createRecurringTransaction(recurring: {
    type: string
    amount: number
    description: string
    category: string
    frequency: string
    next_date: string
    end_date?: string
    auto_add?: boolean
    remind_days_before?: number
  }) {
    const { data } = await this.client.post('/recurring-transactions', recurring)
    return data
  }

  async updateRecurringTransaction(id: string, updates: any) {
    const { data } = await this.client.put(`/recurring-transactions/${id}`, updates)
    return data
  }

  async deleteRecurringTransaction(id: string) {
    const { data } = await this.client.delete(`/recurring-transactions/${id}`)
    return data
  }

  // Cash Flow Forecast
  async getCashFlowForecast(startingBalance: number, forecastDays: number): Promise<CashFlowForecast> {
    const { data } = await this.client.post('/cashflow-forecast', {
      starting_balance: startingBalance,
      forecast_days: forecastDays,
    })
    return data
  }

  // Notifications
  async getNotifications(unreadOnly = false): Promise<{ notifications: Notification[] }> {
    const { data } = await this.client.get(`/notifications?unread_only=${unreadOnly}`)
    return data
  }

  async markNotificationRead(id: string) {
    const { data } = await this.client.put(`/notifications/${id}/read`)
    return data
  }

  async deleteNotification(id: string) {
    const { data } = await this.client.delete(`/notifications/${id}`)
    return data
  }

  // Export
  async exportTransactionsCSV(startDate?: string, endDate?: string) {
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    
    const response = await this.client.get(`/export/transactions/csv?${params}`, {
      responseType: 'blob',
    })
    return response.data
  }

  async exportFinancialReportPDF(year: number, month?: number) {
    const params = new URLSearchParams({ year: year.toString() })
    if (month) params.append('month', month.toString())
    
    const response = await this.client.get(`/export/report/pdf?${params}`, {
      responseType: 'blob',
    })
    return response.data
  }

  async exportTaxDocument(year: number) {
    const response = await this.client.get(`/export/tax-document/${year}`, {
      responseType: 'blob',
    })
    return response.data
  }

  // User Preferences
  async getUserPreferences() {
    const { data } = await this.client.get('/user/preferences')
    return data
  }

  async updateUserPreferences(preferences: {
    currency?: string
    timezone?: string
    country?: string
  }) {
    const { data } = await this.client.put('/user/preferences', preferences)
    return data
  }

  // User Data Management
  async flushUserData() {
    const { data } = await this.client.post('/user/flush')
    return data
  }
}

export const api = new ApiService()
