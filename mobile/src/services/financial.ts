/**
 * Financial Data Service
 */

import { apiClient } from './api';
import type {
  Transaction,
  Debt,
  Goal,
  FinancialHealth,
  ChatRequest,
  ChatResponse,
  AddTransactionRequest,
  AddGoalRequest,
  AddDebtRequest,
  Category,
  CategoryResponse,
  CategoryPath,
} from '../types';

class FinancialService {
  // ============ Chat / AI Agent ============
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return apiClient.post<ChatResponse>('/chat', request);
  }

  // ============ Transactions ============
  async getTransactions(): Promise<Transaction[]> {
    const response = await apiClient.get<{ transactions: Transaction[] }>('/transactions');
    return response.transactions;
  }

  async addTransaction(data: AddTransactionRequest): Promise<Transaction> {
    return apiClient.post<Transaction>('/transactions', data);
  }

  async updateTransaction(id: string, data: Partial<AddTransactionRequest>): Promise<Transaction> {
    return apiClient.put<Transaction>(`/transactions/${id}`, data);
  }

  async deleteTransaction(id: string): Promise<void> {
    return apiClient.delete(`/transactions/${id}`);
  }

  // ============ Financial Health ============
  async getFinancialHealth(): Promise<FinancialHealth> {
    return apiClient.get<FinancialHealth>('/financial-health');
  }

  // ============ Goals ============
  async getGoals(): Promise<{ goals: any[] }> {
    return apiClient.get<{ goals: any[] }>('/goals');
  }

  async addGoal(data: AddGoalRequest): Promise<Goal> {
    return apiClient.post<Goal>('/goals', data);
  }

  async updateGoalProgress(id: string, amount: number): Promise<Goal> {
    return apiClient.put<Goal>(`/goals/${id}/progress`, { amount });
  }

  async deleteGoal(id: string): Promise<void> {
    return apiClient.delete(`/goals/${id}`);
  }

  // ============ Debts & Loans ============
  async getDebts(): Promise<Debt[]> {
    const response = await apiClient.get<{ debts: Debt[] }>('/debts');
    return response.debts;
  }

  async addDebt(data: AddDebtRequest): Promise<Debt> {
    return apiClient.post<Debt>('/debts', data);
  }

  async makePayment(id: string, amount: number): Promise<Debt> {
    return apiClient.post<Debt>(`/debts/${id}/payment`, { amount });
  }

  async deleteDebt(id: string): Promise<void> {
    return apiClient.delete(`/debts/${id}`);
  }

  // ============ Analytics ============
  async getSpendingByCategory(): Promise<any> {
    return apiClient.get('/analytics/spending-by-category');
  }

  // ============ TIER 1: Budgets ============
  async getBudgets(): Promise<{ budgets: any[] }> {
    return apiClient.get('/budgets');
  }

  async getBudgetStatus(budgetId: string): Promise<any> {
    return apiClient.get(`/budgets/${budgetId}/status`);
  }

  async createBudget(data: any): Promise<any> {
    return apiClient.post('/budgets', data);
  }

  async updateBudget(id: string, data: any): Promise<any> {
    return apiClient.put(`/budgets/${id}`, data);
  }

  async deleteBudget(id: string): Promise<void> {
    return apiClient.delete(`/budgets/${id}`);
  }

  // ============ TIER 1: Recurring Transactions ============
  async getRecurringTransactions(): Promise<{ recurring_transactions: any[] }> {
    return apiClient.get('/recurring-transactions');
  }

  async createRecurringTransaction(data: any): Promise<any> {
    return apiClient.post('/recurring-transactions', data);
  }

  async updateRecurringTransaction(id: string, data: any): Promise<any> {
    return apiClient.put(`/recurring-transactions/${id}`, data);
  }

  async deleteRecurringTransaction(id: string): Promise<void> {
    return apiClient.delete(`/recurring-transactions/${id}`);
  }

  // ============ TIER 1: Cash Flow Forecasting ============
  async getCashFlowForecast(data: any): Promise<any> {
    return apiClient.post('/cashflow-forecast', data);
  }

  // ============ TIER 1: Notifications ============
  async getNotifications(): Promise<{ notifications: any[] }> {
    return apiClient.get('/notifications');
  }

  async markNotificationAsRead(id: string): Promise<any> {
    return apiClient.put(`/notifications/${id}/read`, {});
  }

  async deleteNotification(id: string): Promise<void> {
    return apiClient.delete(`/notifications/${id}`);
  }

  // ============ TIER 1: Export ============
  async exportTransactionsCSV(startDate?: string, endDate?: string): Promise<string> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const queryString = params.toString();
    const url = `/export/transactions/csv${queryString ? '?' + queryString : ''}`;
    return apiClient.get(url);
  }

  async exportFinancialReport(year: number, month: number): Promise<string> {
    return apiClient.get(`/export/report/pdf?year=${year}&month=${month}`);
  }

  async exportTaxDocument(taxYear: number): Promise<string> {
    return apiClient.get(`/export/tax-document/${taxYear}`);
  }

  // ============ Accounts ============
  async getAccounts(): Promise<{ accounts: any[] }> {
    return apiClient.get('/accounts');
  }

  async getAccount(id: string): Promise<any> {
    return apiClient.get(`/accounts/${id}`);
  }

  async addAccount(data: any): Promise<any> {
    return apiClient.post('/accounts', data);
  }

  async updateAccount(id: string, data: any): Promise<any> {
    return apiClient.put(`/accounts/${id}`, data);
  }

  async deleteAccount(id: string): Promise<void> {
    return apiClient.delete(`/accounts/${id}`);
  }

  async addCreditCard(data: any): Promise<any> {
    return apiClient.post('/accounts/credit-card', data);
  }

  async updateCreditCard(accountId: string, data: any): Promise<any> {
    return apiClient.put(`/accounts/${accountId}/credit-card`, data);
  }

  // ============ User Preferences ============
  async getUserPreferences(): Promise<any> {
    return apiClient.get('/user/preferences');
  }

  async updateUserPreferences(data: any): Promise<any> {
    return apiClient.put('/user/preferences', data);
  }

  // ============ ADVANCED FEATURES ============
  
  // ============ Hierarchical Categories ============
  async getCategories(): Promise<CategoryResponse> {
    return apiClient.get<CategoryResponse>('/categories');
  }

  async getCategoryPath(category: string): Promise<CategoryPath> {
    return apiClient.get<CategoryPath>(`/categories/${category}/path`);
  }

  async suggestCategory(description: string): Promise<{ category: string; confidence: number }> {
    return apiClient.post('/categories/suggest', { description });
  }

  // Dynamic Budget Adjustments
  async analyzeBudgets(): Promise<any> {
    return apiClient.get('/budgets/analysis');
  }

  async applyBudgetAdjustments(adjustments: any[], autoApply: boolean = false): Promise<any> {
    return apiClient.post('/budgets/apply-adjustments', { 
      adjustments, 
      auto_apply: autoApply 
    });
  }

  // AI-Adjusted Goal Milestones
  async getGoalMilestones(goalId?: string): Promise<any> {
    const url = goalId ? `/goals/${goalId}/milestones` : '/goals/milestones';
    return apiClient.get(url);
  }

  // Financial Simulations
  async runSimulation(scenario: {
    scenario_type: string;
    parameters: any;
    forecast_days?: number;
  }): Promise<any> {
    return apiClient.post('/simulate', scenario);
  }
}

export const financialService = new FinancialService();
