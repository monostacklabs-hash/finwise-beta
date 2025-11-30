/**
 * TypeScript Type Definitions
 */

// User types
export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface UserPreferences {
  currency: string;
  timezone: string;
  country?: string;
}

export interface UpdatePreferencesRequest {
  currency?: string;
  timezone?: string;
  country?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user?: User;
}

// Transaction types
export type TransactionBaseType = 'income' | 'expense' | 'lending' | 'borrowing';
export type TransactionSpecialType = 'default' | 'upcoming' | 'subscription' | 'repetitive' | 'credit' | 'debt';

export interface Transaction {
  id: string;
  user_id: string;
  type: TransactionBaseType;
  special_type?: TransactionSpecialType; // upcoming, subscription, repetitive, credit (lent), debt (borrowed)
  amount: number;
  category: string; // Full path: "food > groceries > fresh_produce"
  category_id?: string; // Category UUID
  parent_category?: string; // Parent category name
  description: string;
  date: string;
  recurring?: boolean;
  paired_transaction_id?: string; // For transfers between accounts
  created_at: string;
}

// Debt/Loan types
export interface Debt {
  id: string;
  user_id: string;
  type: 'debt' | 'loan';
  name: string;
  principal_amount: number;
  remaining_amount: number;
  interest_rate: number;
  start_date: string;
  monthly_payment: number;
  status: 'active' | 'paid_off' | 'defaulted';
  created_at: string;
  updated_at?: string;
}

// Account types
export type AccountType = 'checking' | 'savings' | 'credit_card' | 'investment' | 'cash' | 'other';
export type AccountStatus = 'active' | 'closed' | 'frozen' | 'pending';
export type CardNetwork = 'visa' | 'mastercard' | 'american_express' | 'discover' | 'diners_club' | 'jcb' | 'unionpay' | 'other';

export interface Account {
  id: string;
  user_id: string;
  account_type: AccountType;
  account_name: string;
  institution_name?: string;
  account_number_last4?: string;
  current_balance: number;
  currency: string;
  status: AccountStatus;
  opening_date?: string;
  closing_date?: string;
  interest_rate?: number;
  notes?: string;
  created_at: string;
  updated_at?: string;
  credit_card?: CreditCard;
}

export interface CreditCard {
  id: string;
  account_id: string;
  credit_limit: number;
  available_credit: number;
  apr?: number;
  annual_fee: number;
  late_fee: number;
  foreign_transaction_fee_percent: number;
  statement_balance: number;
  minimum_payment: number;
  statement_date?: string;
  payment_due_date?: string;
  last_payment_date?: string;
  last_payment_amount: number;
  card_network?: CardNetwork;
  card_last4?: string;
  cardholder_name?: string;
  expiration_month?: number;
  expiration_year?: number;
  rewards_program?: string;
  rewards_balance: number;
  cashback_rate?: number;
  grace_period_days: number;
  credit_utilization: number;
  alert_before_due_days: number;
  autopay_enabled: boolean;
  autopay_amount: string;
  created_at: string;
  updated_at?: string;
}

export interface AddAccountRequest {
  account_type: AccountType;
  account_name: string;
  institution_name?: string;
  account_number_last4?: string;
  current_balance?: number;
  currency?: string;
  opening_date?: string;
  interest_rate?: number;
  notes?: string;
}

export interface UpdateAccountRequest {
  account_name?: string;
  current_balance?: number;
  status?: AccountStatus;
  notes?: string;
}

export interface AddCreditCardRequest {
  account_id: string;
  credit_limit: number;
  available_credit: number;
  apr?: number;
  annual_fee?: number;
  statement_balance?: number;
  minimum_payment?: number;
  payment_due_date?: string;
  card_network?: CardNetwork;
  card_last4?: string;
  cardholder_name?: string;
  rewards_program?: string;
  cashback_rate?: number;
}

export interface UpdateCreditCardRequest {
  credit_limit?: number;
  available_credit?: number;
  statement_balance?: number;
  minimum_payment?: number;
  payment_due_date?: string;
  rewards_balance?: number;
}

// Goal types
export interface Goal {
  id: string;
  user_id: string;
  name: string;
  target_amount: number;
  current_amount: number;
  target_date: string;
  priority: number;
  status: 'active' | 'completed' | 'abandoned';
  created_at: string;
  updated_at?: string;
}

// Financial Health
export interface FinancialHealth {
  health_score: number;
  net_worth: number;
  total_income: number;
  total_expenses: number;
  total_debt: number;
  savings_rate: number;
  debt_to_income_ratio: number;
  liquidity_ratio: number;
  assessment: string;
  recommendations: string[];
}

// Chat types
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatResponse {
  response: string;
  tools_used?: string[];
  success: boolean;
  usage?: TokenUsage;
  error?: string;
}

export interface TokenUsage {
  timestamp: string;
  model: string;
  tokens: {
    input: number;
    output: number;
    cached: number;
    total: number;
  };
  costs: {
    input_cost: number;
    output_cost: number;
    cache_cost: number;
    total_cost: number;
    currency: string;
  };
  context_usage: {
    used: number;
    available: number;
    percentage: number;
  };
}

// API Request/Response types
export interface LoginRequest {
  username: string; // This is the email address (kept as username for form compatibility)
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface ChatRequest {
  message: string;
  chat_history?: ChatMessage[];
}

export interface AddTransactionRequest {
  type: TransactionBaseType;
  special_type?: TransactionSpecialType;
  amount: number;
  category: string; // Can be full path or just name
  category_id?: string;
  description: string;
  date?: string;
  account_id?: string;
  paired_transaction_id?: string;
}

export interface AddGoalRequest {
  name: string;
  target_amount: number;
  target_date: string;
  priority?: number;
}

export interface AddDebtRequest {
  type: 'debt' | 'loan';
  name: string;
  principal_amount: number;
  remaining_amount: number;
  interest_rate: number;
  start_date: string;
  monthly_payment: number;
}

// TIER 1 FEATURES - Budget Management
export interface Budget {
  id: string;
  user_id: string;
  category: string;
  amount: number;
  period: 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  alert_threshold: number;
  start_date: string;
  end_date?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface BudgetStatus {
  budget_id: string;
  category: string;
  budgeted_amount: number;
  actual_spent: number;
  remaining: number;
  percentage_used: number;
  is_overspent: boolean;
  period_start: string;
  period_end: string;
}

export interface CreateBudgetRequest {
  category: string;
  amount: number;
  period: 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  alert_threshold?: number;
  start_date?: string;
}

export interface UpdateBudgetRequest {
  category?: string;
  amount?: number;
  period?: string;
  alert_threshold?: number;
  is_active?: boolean;
}

// TIER 1 FEATURES - Recurring Transactions
export interface RecurringTransaction {
  id: string;
  user_id: string;
  type: 'income' | 'expense';
  amount: number;
  category: string;
  description: string;
  frequency: 'daily' | 'weekly' | 'bi_weekly' | 'monthly' | 'quarterly' | 'yearly';
  next_date: string;
  reminder_days_before: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface CreateRecurringTransactionRequest {
  type: 'income' | 'expense';
  amount: number;
  category: string;
  description: string;
  frequency: 'daily' | 'weekly' | 'bi_weekly' | 'monthly' | 'quarterly' | 'yearly';
  next_date: string;
  reminder_days_before?: number;
}

export interface UpdateRecurringTransactionRequest {
  type?: 'income' | 'expense';
  amount?: number;
  category?: string;
  description?: string;
  frequency?: string;
  next_date?: string;
  reminder_days_before?: number;
  is_active?: boolean;
}

// TIER 1 FEATURES - Cash Flow Forecasting
export interface CashFlowForecast {
  starting_balance: number;
  forecast_days: number;
  daily_balances?: DailyBalance[];
  summary_periods?: SummaryPeriod[];
  runway_days: number | null;
  min_balance: number;
  min_balance_date: string | null;
  warnings?: string[];
}

export interface DailyBalance {
  date: string;
  balance: number;
  income: number;
  expenses: number;
}

export interface SummaryPeriod {
  period: string;
  period_start: string;
  period_end: string;
  starting_balance: number;
  ending_balance: number;
  total_income: number;
  total_expenses: number;
  net_change: number;
}

export interface CashFlowForecastRequest {
  starting_balance: number;
  forecast_days?: number;
}

// TIER 1 FEATURES - Notifications
export interface Notification {
  id: string;
  user_id: string;
  type: 'bill_reminder' | 'budget_alert' | 'goal_milestone' | 'unusual_spending' | 'low_balance' | 'info';
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high';
  is_read: boolean;
  action_required: boolean;
  related_id?: string;
  created_at: string;
}

export interface UpdateNotificationRequest {
  is_read: boolean;
}

// TIER 1 FEATURES - Export
export interface ExportTransactionsRequest {
  start_date?: string;
  end_date?: string;
  format?: 'csv' | 'json';
}

export interface ExportReportRequest {
  year: number;
  month: number;
  format?: 'pdf' | 'html';
}

export interface ExportTaxDocumentRequest {
  tax_year: number;
}


// ============================================================================
// CATEGORY SYSTEM - Hierarchical Categories
// ============================================================================

export interface Category {
  id: string;
  name: string; // snake_case identifier (e.g., "fresh_produce")
  display_name: string; // Human-readable (e.g., "Fresh Produce")
  parent_category?: string; // Parent category name
  icon?: string;
  color?: string;
  usage_count?: number;
  ai_suggested?: boolean;
  is_default?: boolean;
  children?: Category[]; // Subcategories
}

export interface CategoryPath {
  full_path: string; // "food > groceries > fresh_produce"
  categories: string[]; // ["food", "groceries", "fresh_produce"]
  root: string; // "food"
}

export interface CategoryResponse {
  categories: Category[];
  hierarchy: Record<string, Category[]>; // parent_name -> children
}
