/**
 * Financial Service Unit Tests
 * Tests API integration layer
 */

import { financialService } from '../../src/services/financial';
import { apiClient } from '../../src/services/api';

// Mock the API client
jest.mock('../../src/services/api');

describe('FinancialService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Chat / AI Agent', () => {
    it('should send chat message', async () => {
      const mockResponse = {
        response: 'Test response',
        tools_used: ['get_transactions'],
        success: true,
      };
      (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

      const result = await financialService.sendMessage({
        message: 'What is my balance?',
        chat_history: [],
      });

      expect(apiClient.post).toHaveBeenCalledWith('/chat', {
        message: 'What is my balance?',
        chat_history: [],
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Transactions', () => {
    it('should get transactions', async () => {
      const mockTransactions = [
        { id: '1', type: 'expense', amount: 50, description: 'Groceries', category: 'Food', date: '2025-11-16' },
      ];
      (apiClient.get as jest.Mock).mockResolvedValue({ transactions: mockTransactions });

      const result = await financialService.getTransactions();

      expect(apiClient.get).toHaveBeenCalledWith('/transactions');
      expect(result).toEqual(mockTransactions);
    });

    it('should add transaction', async () => {
      const mockTransaction = { id: '1', type: 'expense', amount: 50, description: 'Groceries', category: 'Food', date: '2025-11-16' };
      (apiClient.post as jest.Mock).mockResolvedValue(mockTransaction);

      const result = await financialService.addTransaction({
        type: 'expense',
        amount: 50,
        category: 'Food',
        description: 'Groceries',
      });

      expect(apiClient.post).toHaveBeenCalledWith('/transactions', {
        type: 'expense',
        amount: 50,
        category: 'Food',
        description: 'Groceries',
      });
      expect(result).toEqual(mockTransaction);
    });

    it('should delete transaction', async () => {
      (apiClient.delete as jest.Mock).mockResolvedValue({ success: true });

      await financialService.deleteTransaction('123');

      expect(apiClient.delete).toHaveBeenCalledWith('/transactions/123');
    });
  });

  describe('Financial Health', () => {
    it('should get financial health metrics', async () => {
      const mockHealth = {
        health_score: 75,
        net_worth: 10000,
        total_income: 50000,
        total_expenses: 30000,
        total_debt: 10000,
        savings_rate: 0.4,
        debt_to_income_ratio: 0.2,
        liquidity_ratio: 6.67,
        assessment: 'Good financial health',
        recommendations: ['Save more', 'Reduce debt'],
      };
      (apiClient.get as jest.Mock).mockResolvedValue(mockHealth);

      const result = await financialService.getFinancialHealth();

      expect(apiClient.get).toHaveBeenCalledWith('/financial-health');
      expect(result).toEqual(mockHealth);
    });
  });

  describe('Goals', () => {
    it('should get goals', async () => {
      const mockGoals = [
        { id: '1', name: 'Emergency Fund', target_amount: 10000, current_amount: 5000, target_date: '2026-12-31', status: 'active' },
      ];
      (apiClient.get as jest.Mock).mockResolvedValue({ goals: mockGoals });

      const result = await financialService.getGoals();

      expect(apiClient.get).toHaveBeenCalledWith('/goals');
      expect(result).toEqual({ goals: mockGoals });
    });

    it('should add goal', async () => {
      const mockGoal = { id: '1', name: 'Vacation', target_amount: 5000, current_amount: 0, target_date: '2026-06-01', status: 'active' };
      (apiClient.post as jest.Mock).mockResolvedValue(mockGoal);

      const result = await financialService.addGoal({
        name: 'Vacation',
        target_amount: 5000,
        target_date: '2026-06-01',
      });

      expect(apiClient.post).toHaveBeenCalledWith('/goals', {
        name: 'Vacation',
        target_amount: 5000,
        target_date: '2026-06-01',
      });
      expect(result).toEqual(mockGoal);
    });

    it('should update goal progress', async () => {
      const mockGoal = { id: '1', name: 'Vacation', target_amount: 5000, current_amount: 500, target_date: '2026-06-01', status: 'active' };
      (apiClient.put as jest.Mock).mockResolvedValue(mockGoal);

      const result = await financialService.updateGoalProgress('1', 500);

      expect(apiClient.put).toHaveBeenCalledWith('/goals/1/progress', { amount: 500 });
      expect(result).toEqual(mockGoal);
    });

    it('should delete goal', async () => {
      (apiClient.delete as jest.Mock).mockResolvedValue({ success: true });

      await financialService.deleteGoal('123');

      expect(apiClient.delete).toHaveBeenCalledWith('/goals/123');
    });
  });

  describe('Debts & Loans', () => {
    it('should get debts', async () => {
      const mockDebts = [
        { id: '1', type: 'debt', name: 'Credit Card', remaining_amount: 5000, interest_rate: 18.5, monthly_payment: 200, status: 'active' },
      ];
      (apiClient.get as jest.Mock).mockResolvedValue({ debts: mockDebts });

      const result = await financialService.getDebts();

      expect(apiClient.get).toHaveBeenCalledWith('/debts');
      expect(result).toEqual(mockDebts);
    });

    it('should add debt', async () => {
      const mockDebt = { id: '1', type: 'debt', name: 'Student Loan', remaining_amount: 20000, interest_rate: 5.5, monthly_payment: 300, status: 'active' };
      (apiClient.post as jest.Mock).mockResolvedValue(mockDebt);

      const result = await financialService.addDebt({
        type: 'debt',
        name: 'Student Loan',
        principal_amount: 20000,
        remaining_amount: 20000,
        interest_rate: 5.5,
        start_date: '2020-01-01',
        monthly_payment: 300,
      });

      expect(apiClient.post).toHaveBeenCalled();
      expect(result).toEqual(mockDebt);
    });

    it('should make debt payment', async () => {
      const mockDebt = { id: '1', type: 'debt', name: 'Credit Card', remaining_amount: 4500, interest_rate: 18.5, monthly_payment: 200, status: 'active' };
      (apiClient.post as jest.Mock).mockResolvedValue(mockDebt);

      const result = await financialService.makePayment('1', 500);

      expect(apiClient.post).toHaveBeenCalledWith('/debts/1/payment', { amount: 500 });
      expect(result).toEqual(mockDebt);
    });

    it('should delete debt', async () => {
      (apiClient.delete as jest.Mock).mockResolvedValue({ success: true });

      await financialService.deleteDebt('123');

      expect(apiClient.delete).toHaveBeenCalledWith('/debts/123');
    });
  });

  describe('Budgets', () => {
    it('should get budgets', async () => {
      const mockBudgets = [
        { id: '1', category: 'Food', amount: 500, period: 'monthly', alert_threshold: 0.9, is_active: true },
      ];
      (apiClient.get as jest.Mock).mockResolvedValue({ budgets: mockBudgets });

      const result = await financialService.getBudgets();

      expect(apiClient.get).toHaveBeenCalledWith('/budgets');
      expect(result).toEqual({ budgets: mockBudgets });
    });

    it('should create budget', async () => {
      const mockBudget = { id: '1', category: 'Entertainment', amount: 200, period: 'monthly', alert_threshold: 0.9, is_active: true };
      (apiClient.post as jest.Mock).mockResolvedValue(mockBudget);

      const result = await financialService.createBudget({
        category: 'Entertainment',
        amount: 200,
        period: 'monthly',
      });

      expect(apiClient.post).toHaveBeenCalledWith('/budgets', {
        category: 'Entertainment',
        amount: 200,
        period: 'monthly',
      });
      expect(result).toEqual(mockBudget);
    });

    it('should update budget', async () => {
      (apiClient.put as jest.Mock).mockResolvedValue({ success: true });

      await financialService.updateBudget('1', { amount: 250 });

      expect(apiClient.put).toHaveBeenCalledWith('/budgets/1', { amount: 250 });
    });

    it('should delete budget', async () => {
      (apiClient.delete as jest.Mock).mockResolvedValue({ success: true });

      await financialService.deleteBudget('123');

      expect(apiClient.delete).toHaveBeenCalledWith('/budgets/123');
    });
  });

  describe('Recurring Transactions', () => {
    it('should get recurring transactions', async () => {
      const mockRecurring = [
        { id: '1', type: 'expense', amount: 100, description: 'Netflix', category: 'Entertainment', frequency: 'monthly', next_date: '2025-12-01' },
      ];
      (apiClient.get as jest.Mock).mockResolvedValue({ recurring_transactions: mockRecurring });

      const result = await financialService.getRecurringTransactions();

      expect(apiClient.get).toHaveBeenCalledWith('/recurring-transactions');
      expect(result).toEqual({ recurring_transactions: mockRecurring });
    });

    it('should create recurring transaction', async () => {
      const mockRecurring = { id: '1', type: 'expense', amount: 50, description: 'Gym', category: 'Health', frequency: 'monthly', next_date: '2025-12-01' };
      (apiClient.post as jest.Mock).mockResolvedValue(mockRecurring);

      const result = await financialService.createRecurringTransaction({
        type: 'expense',
        amount: 50,
        description: 'Gym',
        category: 'Health',
        frequency: 'monthly',
        next_date: '2025-12-01',
      });

      expect(apiClient.post).toHaveBeenCalled();
      expect(result).toEqual(mockRecurring);
    });

    it('should update recurring transaction', async () => {
      (apiClient.put as jest.Mock).mockResolvedValue({ success: true });

      await financialService.updateRecurringTransaction('1', { amount: 60 });

      expect(apiClient.put).toHaveBeenCalledWith('/recurring-transactions/1', { amount: 60 });
    });

    it('should delete recurring transaction', async () => {
      (apiClient.delete as jest.Mock).mockResolvedValue({ success: true });

      await financialService.deleteRecurringTransaction('123');

      expect(apiClient.delete).toHaveBeenCalledWith('/recurring-transactions/123');
    });
  });

  describe('Cash Flow Forecasting', () => {
    it('should get cash flow forecast', async () => {
      const mockForecast = {
        starting_balance: 5000,
        forecast_days: 90,
        daily_balances: [],
        runway_days: 180,
        min_balance: 3000,
        min_balance_date: '2026-01-15',
        warnings: [],
      };
      (apiClient.post as jest.Mock).mockResolvedValue(mockForecast);

      const result = await financialService.getCashFlowForecast({
        starting_balance: 5000,
        forecast_days: 90,
      });

      expect(apiClient.post).toHaveBeenCalledWith('/cashflow-forecast', {
        starting_balance: 5000,
        forecast_days: 90,
      });
      expect(result).toEqual(mockForecast);
    });
  });

  describe('Notifications', () => {
    it('should get notifications', async () => {
      const mockNotifications = [
        { id: '1', type: 'budget_alert', title: 'Budget Alert', message: 'You exceeded your food budget', priority: 'high', is_read: false },
      ];
      (apiClient.get as jest.Mock).mockResolvedValue({ notifications: mockNotifications });

      const result = await financialService.getNotifications();

      expect(apiClient.get).toHaveBeenCalledWith('/notifications');
      expect(result).toEqual({ notifications: mockNotifications });
    });

    it('should mark notification as read', async () => {
      (apiClient.put as jest.Mock).mockResolvedValue({ success: true });

      await financialService.markNotificationAsRead('123');

      expect(apiClient.put).toHaveBeenCalledWith('/notifications/123/read', {});
    });

    it('should delete notification', async () => {
      (apiClient.delete as jest.Mock).mockResolvedValue({ success: true });

      await financialService.deleteNotification('123');

      expect(apiClient.delete).toHaveBeenCalledWith('/notifications/123');
    });
  });

  describe('Accounts', () => {
    it('should get accounts', async () => {
      const mockAccounts = [
        { id: '1', account_type: 'checking', account_name: 'Main Checking', current_balance: 5000, currency: 'USD', status: 'active' },
      ];
      (apiClient.get as jest.Mock).mockResolvedValue({ accounts: mockAccounts });

      const result = await financialService.getAccounts();

      expect(apiClient.get).toHaveBeenCalledWith('/accounts');
      expect(result).toEqual({ accounts: mockAccounts });
    });

    it('should add account', async () => {
      const mockAccount = { id: '1', account_type: 'savings', account_name: 'Emergency Fund', current_balance: 10000, currency: 'USD', status: 'active' };
      (apiClient.post as jest.Mock).mockResolvedValue(mockAccount);

      const result = await financialService.addAccount({
        account_type: 'savings',
        account_name: 'Emergency Fund',
        current_balance: 10000,
      });

      expect(apiClient.post).toHaveBeenCalled();
      expect(result).toEqual(mockAccount);
    });

    it('should update account', async () => {
      (apiClient.put as jest.Mock).mockResolvedValue({ success: true });

      await financialService.updateAccount('1', { current_balance: 5500 });

      expect(apiClient.put).toHaveBeenCalledWith('/accounts/1', { current_balance: 5500 });
    });

    it('should delete account', async () => {
      (apiClient.delete as jest.Mock).mockResolvedValue({ success: true });

      await financialService.deleteAccount('123');

      expect(apiClient.delete).toHaveBeenCalledWith('/accounts/123');
    });
  });

  describe('User Preferences', () => {
    it('should get user preferences', async () => {
      const mockPreferences = { currency: 'USD', timezone: 'America/New_York', country: 'US' };
      (apiClient.get as jest.Mock).mockResolvedValue(mockPreferences);

      const result = await financialService.getUserPreferences();

      expect(apiClient.get).toHaveBeenCalledWith('/user/preferences');
      expect(result).toEqual(mockPreferences);
    });

    it('should update user preferences', async () => {
      (apiClient.put as jest.Mock).mockResolvedValue({ success: true });

      await financialService.updateUserPreferences({ currency: 'EUR' });

      expect(apiClient.put).toHaveBeenCalledWith('/user/preferences', { currency: 'EUR' });
    });
  });

  describe('Advanced Features', () => {
    it('should get categories', async () => {
      const mockCategories = [{ id: '1', name: 'Food', parent_id: null }];
      (apiClient.get as jest.Mock).mockResolvedValue(mockCategories);

      const result = await financialService.getCategories();

      expect(apiClient.get).toHaveBeenCalledWith('/categories');
      expect(result).toEqual(mockCategories);
    });

    it('should analyze budgets', async () => {
      const mockAnalysis = { adjustments: [], recommendations: [] };
      (apiClient.get as jest.Mock).mockResolvedValue(mockAnalysis);

      const result = await financialService.analyzeBudgets();

      expect(apiClient.get).toHaveBeenCalledWith('/budgets/analysis');
      expect(result).toEqual(mockAnalysis);
    });

    it('should get goal milestones', async () => {
      const mockMilestones = [{ goal_id: '1', milestone: 25, achieved: true }];
      (apiClient.get as jest.Mock).mockResolvedValue(mockMilestones);

      const result = await financialService.getGoalMilestones();

      expect(apiClient.get).toHaveBeenCalledWith('/goals/milestones');
      expect(result).toEqual(mockMilestones);
    });

    it('should run simulation', async () => {
      const mockSimulation = { baseline: {}, scenario: {}, impact: {} };
      (apiClient.post as jest.Mock).mockResolvedValue(mockSimulation);

      const result = await financialService.runSimulation({
        scenario_type: 'income_change',
        parameters: { new_income: 60000 },
      });

      expect(apiClient.post).toHaveBeenCalledWith('/simulate', {
        scenario_type: 'income_change',
        parameters: { new_income: 60000 },
      });
      expect(result).toEqual(mockSimulation);
    });
  });
});
