-- Add comprehensive descriptions to all tables and columns for AI agent comprehension
-- This migration adds SQL COMMENT statements to document the database schema
-- This helps AI agents understand the purpose and usage of each table and column

-- ============================================================================
-- USERS TABLE
-- ============================================================================

COMMENT ON TABLE users IS 'User accounts - stores authentication and personal information for each user of the financial planning system';

COMMENT ON COLUMN users.id IS 'Unique user identifier (UUID format)';
COMMENT ON COLUMN users.email IS 'User email address - used for login and notifications (unique, indexed)';
COMMENT ON COLUMN users.password_hash IS 'Hashed password for authentication - never store plain text passwords';
COMMENT ON COLUMN users.name IS 'User full name or display name';
COMMENT ON COLUMN users.timezone IS 'User timezone in IANA format (e.g., America/New_York, Asia/Kolkata) - used for date/time localization';
COMMENT ON COLUMN users.currency IS 'User preferred currency code (e.g., USD, EUR, INR) - all financial amounts are displayed in this currency';
COMMENT ON COLUMN users.country IS 'User country code (e.g., US, IN, GB) - used for localization and regulations';
COMMENT ON COLUMN users.created_at IS 'Timestamp when the user account was created';
COMMENT ON COLUMN users.updated_at IS 'Timestamp when the user account was last modified';

-- ============================================================================
-- TRANSACTIONS TABLE
-- ============================================================================

COMMENT ON TABLE transactions IS 'Financial transactions - records all income, expenses, lending, and borrowing activities for users';

COMMENT ON COLUMN transactions.id IS 'Unique transaction identifier (UUID format)';
COMMENT ON COLUMN transactions.user_id IS 'Foreign key to users table - identifies which user this transaction belongs to (indexed)';
COMMENT ON COLUMN transactions.account_id IS 'Optional foreign key to accounts table - links transaction to a specific bank account (indexed)';
COMMENT ON COLUMN transactions.type IS 'Transaction type: income (money earned), expense (money spent), lending (money lent to others), borrowing (money borrowed)';
COMMENT ON COLUMN transactions.amount IS 'Transaction amount in the user currency - always positive, type determines if it increases or decreases net worth';
COMMENT ON COLUMN transactions.description IS 'User-provided description of the transaction (e.g., "Groceries at Whole Foods", "Freelance payment")';
COMMENT ON COLUMN transactions.category IS 'Category for grouping transactions (e.g., food, transport, entertainment, salary) - used for spending analysis';
COMMENT ON COLUMN transactions.date IS 'Date when the transaction occurred - can be different from created_at for backdated entries';
COMMENT ON COLUMN transactions.recurring IS 'Boolean flag indicating if this is a recurring transaction (deprecated - use recurring_transactions table instead)';
COMMENT ON COLUMN transactions.extra_data IS 'JSON string for storing additional custom fields or metadata';
COMMENT ON COLUMN transactions.created_at IS 'Timestamp when this transaction record was created in the system';

-- ============================================================================
-- ACCOUNTS TABLE
-- ============================================================================

COMMENT ON TABLE accounts IS 'Bank accounts - tracks checking, savings, credit cards, investment accounts, and other financial accounts';

COMMENT ON COLUMN accounts.id IS 'Unique account identifier (UUID format)';
COMMENT ON COLUMN accounts.user_id IS 'Foreign key to users table - identifies which user owns this account (indexed)';
COMMENT ON COLUMN accounts.account_type IS 'Type of account: checking, savings, credit_card, investment, cash, or other';
COMMENT ON COLUMN accounts.account_name IS 'User-friendly name for the account (e.g., "Chase Checking", "Emergency Savings Fund")';
COMMENT ON COLUMN accounts.institution_name IS 'Name of the bank or financial institution (e.g., "Chase Bank", "Wells Fargo")';
COMMENT ON COLUMN accounts.account_number_last4 IS 'Last 4 digits of account number for identification - stored for security (never store full account numbers)';
COMMENT ON COLUMN accounts.current_balance IS 'Current account balance in user currency - updated when transactions are added or account is synced';
COMMENT ON COLUMN accounts.currency IS 'Currency code for this account (e.g., USD, EUR) - may differ from user default currency';
COMMENT ON COLUMN accounts.status IS 'Account status: active (currently in use), closed (no longer active), frozen (temporarily suspended), pending (awaiting activation)';
COMMENT ON COLUMN accounts.opening_date IS 'Date when the account was opened at the financial institution';
COMMENT ON COLUMN accounts.closing_date IS 'Date when the account was closed (null if still active)';
COMMENT ON COLUMN accounts.interest_rate IS 'Annual interest rate as decimal (e.g., 0.025 for 2.5%) - applicable for savings accounts';
COMMENT ON COLUMN accounts.notes IS 'User notes or additional information about this account';
COMMENT ON COLUMN accounts.extra_data IS 'JSON string for storing custom fields or additional metadata';
COMMENT ON COLUMN accounts.created_at IS 'Timestamp when this account was added to the system';
COMMENT ON COLUMN accounts.updated_at IS 'Timestamp when this account was last modified';

-- ============================================================================
-- CREDIT CARDS TABLE
-- ============================================================================

COMMENT ON TABLE credit_cards IS 'Credit card details - extends accounts table with credit-card-specific fields like credit limit, APR, payment dates, and rewards';

COMMENT ON COLUMN credit_cards.id IS 'Unique credit card record identifier (UUID format)';
COMMENT ON COLUMN credit_cards.account_id IS 'Foreign key to accounts table - links to the parent credit card account (unique, indexed)';
COMMENT ON COLUMN credit_cards.credit_limit IS 'Total credit limit available on this card';
COMMENT ON COLUMN credit_cards.available_credit IS 'Currently available credit (credit_limit minus current balance)';
COMMENT ON COLUMN credit_cards.apr IS 'Annual Percentage Rate - interest rate charged on unpaid balances (as decimal, e.g., 0.1999 for 19.99%)';
COMMENT ON COLUMN credit_cards.annual_fee IS 'Yearly fee charged for having this credit card';
COMMENT ON COLUMN credit_cards.late_fee IS 'Fee charged when payment is late';
COMMENT ON COLUMN credit_cards.foreign_transaction_fee_percent IS 'Fee percentage charged on foreign currency transactions (e.g., 0.03 for 3%)';
COMMENT ON COLUMN credit_cards.statement_balance IS 'Balance shown on the most recent statement';
COMMENT ON COLUMN credit_cards.minimum_payment IS 'Minimum payment amount due for the current billing cycle';
COMMENT ON COLUMN credit_cards.statement_date IS 'Date when the statement is generated each billing cycle';
COMMENT ON COLUMN credit_cards.payment_due_date IS 'Date when payment is due - used for bill reminders (indexed for efficient querying of upcoming due dates)';
COMMENT ON COLUMN credit_cards.last_payment_date IS 'Date of the most recent payment made';
COMMENT ON COLUMN credit_cards.last_payment_amount IS 'Amount of the most recent payment';
COMMENT ON COLUMN credit_cards.card_network IS 'Card network/issuer: visa, mastercard, american_express, discover, diners_club, jcb, unionpay, other';
COMMENT ON COLUMN credit_cards.card_last4 IS 'Last 4 digits of the credit card number for identification';
COMMENT ON COLUMN credit_cards.cardholder_name IS 'Name printed on the credit card';
COMMENT ON COLUMN credit_cards.expiration_month IS 'Card expiration month (1-12)';
COMMENT ON COLUMN credit_cards.expiration_year IS 'Card expiration year (4-digit format, e.g., 2027)';
COMMENT ON COLUMN credit_cards.rewards_program IS 'Type of rewards program (e.g., "Cash Back", "Points", "Miles")';
COMMENT ON COLUMN credit_cards.rewards_balance IS 'Current rewards balance - points, miles, or cash back amount accumulated';
COMMENT ON COLUMN credit_cards.cashback_rate IS 'Cash back rate as decimal (e.g., 0.015 for 1.5% cash back)';
COMMENT ON COLUMN credit_cards.grace_period_days IS 'Number of days before interest is charged on new purchases (typically 21-25 days)';
COMMENT ON COLUMN credit_cards.credit_utilization IS 'Credit utilization percentage - calculated as (balance / credit_limit) * 100 - important for credit score';
COMMENT ON COLUMN credit_cards.alert_before_due_days IS 'Number of days before due date to send payment reminder (default 3 days)';
COMMENT ON COLUMN credit_cards.autopay_enabled IS 'Whether automatic payments are enabled for this card';
COMMENT ON COLUMN credit_cards.autopay_amount IS 'Autopay setting: minimum (pay minimum), statement_balance (pay full statement), full_balance (pay entire balance), custom (fixed amount)';
COMMENT ON COLUMN credit_cards.extra_data IS 'JSON string for custom fields and additional metadata';
COMMENT ON COLUMN credit_cards.created_at IS 'Timestamp when this credit card record was created';
COMMENT ON COLUMN credit_cards.updated_at IS 'Timestamp when this credit card record was last modified';

-- ============================================================================
-- DEBTS AND LOANS TABLE
-- ============================================================================

COMMENT ON TABLE debts_loans IS 'Debts and loans - tracks money owed (debts) and money lent to others (loans) with interest rates and payment schedules';

COMMENT ON COLUMN debts_loans.id IS 'Unique debt/loan identifier (UUID format)';
COMMENT ON COLUMN debts_loans.user_id IS 'Foreign key to users table - identifies which user this debt/loan belongs to (indexed)';
COMMENT ON COLUMN debts_loans.type IS 'Type: debt (money user owes to others), loan (money user lent to others)';
COMMENT ON COLUMN debts_loans.name IS 'Name or description of the debt/loan (e.g., "Student Loan", "Credit Card Debt", "Loan to John")';
COMMENT ON COLUMN debts_loans.principal_amount IS 'Original amount borrowed or lent';
COMMENT ON COLUMN debts_loans.remaining_amount IS 'Current outstanding balance - decreases as payments are made';
COMMENT ON COLUMN debts_loans.interest_rate IS 'Annual interest rate as percentage (e.g., 5.5 for 5.5% APR)';
COMMENT ON COLUMN debts_loans.start_date IS 'Date when the debt/loan was initiated';
COMMENT ON COLUMN debts_loans.monthly_payment IS 'Regular monthly payment amount';
COMMENT ON COLUMN debts_loans.status IS 'Status: active (currently being paid), paid_off (fully paid), defaulted (failed to pay)';
COMMENT ON COLUMN debts_loans.extra_data IS 'JSON string for repayment schedule, additional terms, or custom metadata';
COMMENT ON COLUMN debts_loans.created_at IS 'Timestamp when this debt/loan record was created';
COMMENT ON COLUMN debts_loans.updated_at IS 'Timestamp when this debt/loan record was last modified';

-- ============================================================================
-- GOALS TABLE
-- ============================================================================

COMMENT ON TABLE goals IS 'Financial goals - tracks savings targets like emergency funds, vacations, down payments, or other financial objectives';

COMMENT ON COLUMN goals.id IS 'Unique goal identifier (UUID format)';
COMMENT ON COLUMN goals.user_id IS 'Foreign key to users table - identifies which user this goal belongs to (indexed)';
COMMENT ON COLUMN goals.name IS 'Goal name or description (e.g., "Emergency Fund", "Vacation to Japan", "Down Payment")';
COMMENT ON COLUMN goals.target_amount IS 'Target amount to save for this goal';
COMMENT ON COLUMN goals.current_amount IS 'Amount saved so far towards this goal - updated manually or automatically';
COMMENT ON COLUMN goals.target_date IS 'Target date to achieve this goal';
COMMENT ON COLUMN goals.status IS 'Status: active (currently working towards), completed (goal achieved), abandoned (user stopped pursuing)';
COMMENT ON COLUMN goals.priority IS 'Priority level for this goal (1=lowest, higher numbers=higher priority) - used for ranking multiple goals';
COMMENT ON COLUMN goals.extra_data IS 'JSON string for custom fields or additional metadata';
COMMENT ON COLUMN goals.created_at IS 'Timestamp when this goal was created';
COMMENT ON COLUMN goals.updated_at IS 'Timestamp when this goal was last modified';

-- ============================================================================
-- LOGS TABLE
-- ============================================================================

COMMENT ON TABLE logs IS 'Activity logs - audit trail of user actions and system events for security and debugging';

COMMENT ON COLUMN logs.id IS 'Unique log entry identifier (UUID format)';
COMMENT ON COLUMN logs.user_id IS 'Foreign key to users table - identifies which user performed the action (indexed)';
COMMENT ON COLUMN logs.action IS 'Action performed (e.g., "login", "add_transaction", "update_goal", "delete_account")';
COMMENT ON COLUMN logs.details IS 'JSON string with detailed information about the action including parameters and results';
COMMENT ON COLUMN logs.category IS 'Log category for filtering (e.g., "auth", "transaction", "goal", "general")';
COMMENT ON COLUMN logs.ip_address IS 'IP address from which the action was performed - for security auditing';
COMMENT ON COLUMN logs.created_at IS 'Timestamp when the action was performed (indexed for efficient time-based queries)';

-- ============================================================================
-- INSIGHTS TABLE
-- ============================================================================

COMMENT ON TABLE insights IS 'AI-generated insights - personalized financial recommendations and observations generated by the AI agent';

COMMENT ON COLUMN insights.id IS 'Unique insight identifier (UUID format)';
COMMENT ON COLUMN insights.user_id IS 'Foreign key to users table - identifies which user this insight is for (indexed)';
COMMENT ON COLUMN insights.type IS 'Insight type: debt (debt-related advice), savings (savings recommendations), spending (spending patterns), goal (goal progress), general (other insights)';
COMMENT ON COLUMN insights.message IS 'The insight message text - explains the observation or recommendation to the user';
COMMENT ON COLUMN insights.priority IS 'Priority level (1=low, 2=medium, 3=high) - higher priority insights shown first';
COMMENT ON COLUMN insights.is_read IS 'Boolean flag indicating if the user has read this insight';
COMMENT ON COLUMN insights.extra_data IS 'JSON string with supporting data, calculations, or additional context';
COMMENT ON COLUMN insights.created_at IS 'Timestamp when this insight was generated (indexed)';

-- ============================================================================
-- BUDGETS TABLE
-- ============================================================================

COMMENT ON TABLE budgets IS 'Budgets - spending limits by category for monthly, weekly, or yearly periods';

COMMENT ON COLUMN budgets.id IS 'Unique budget identifier (UUID format)';
COMMENT ON COLUMN budgets.user_id IS 'Foreign key to users table - identifies which user this budget belongs to (indexed)';
COMMENT ON COLUMN budgets.category IS 'Category this budget applies to (e.g., food, transport, entertainment) - must match transaction categories (indexed)';
COMMENT ON COLUMN budgets.amount IS 'Budget limit amount for this category in the specified period';
COMMENT ON COLUMN budgets.period IS 'Budget period: monthly (most common), weekly, or yearly';
COMMENT ON COLUMN budgets.start_date IS 'Date when this budget becomes effective';
COMMENT ON COLUMN budgets.end_date IS 'Date when this budget expires (null means ongoing/indefinite)';
COMMENT ON COLUMN budgets.is_active IS 'Boolean flag indicating if this budget is currently active';
COMMENT ON COLUMN budgets.alert_threshold IS 'Percentage of budget at which to send alert (e.g., 0.9 for 90%) - triggers notification when spending reaches this level';
COMMENT ON COLUMN budgets.extra_data IS 'JSON string for custom fields or additional metadata';
COMMENT ON COLUMN budgets.created_at IS 'Timestamp when this budget was created';
COMMENT ON COLUMN budgets.updated_at IS 'Timestamp when this budget was last modified';

-- ============================================================================
-- RECURRING TRANSACTIONS TABLE
-- ============================================================================

COMMENT ON TABLE recurring_transactions IS 'Recurring transactions - scheduled bills, subscriptions, and regular income like salary';

COMMENT ON COLUMN recurring_transactions.id IS 'Unique recurring transaction identifier (UUID format)';
COMMENT ON COLUMN recurring_transactions.user_id IS 'Foreign key to users table - identifies which user this recurring transaction belongs to (indexed)';
COMMENT ON COLUMN recurring_transactions.type IS 'Transaction type: income (recurring earnings like salary), expense (recurring bills like rent), lending, or borrowing';
COMMENT ON COLUMN recurring_transactions.amount IS 'Amount for each occurrence of this recurring transaction';
COMMENT ON COLUMN recurring_transactions.description IS 'Description (e.g., "Netflix Subscription", "Monthly Salary", "Rent Payment")';
COMMENT ON COLUMN recurring_transactions.category IS 'Category for this recurring transaction - used for budgeting and analysis';
COMMENT ON COLUMN recurring_transactions.frequency IS 'How often this transaction occurs: daily, weekly, biweekly, monthly, quarterly, or yearly';
COMMENT ON COLUMN recurring_transactions.next_date IS 'Next scheduled date for this transaction - updated after each occurrence (indexed for efficient scheduling queries)';
COMMENT ON COLUMN recurring_transactions.end_date IS 'Date when this recurring transaction stops (null means indefinite)';
COMMENT ON COLUMN recurring_transactions.is_active IS 'Boolean flag indicating if this recurring transaction is currently active';
COMMENT ON COLUMN recurring_transactions.remind_days_before IS 'Number of days before the transaction to send a reminder notification (default 3 days)';
COMMENT ON COLUMN recurring_transactions.auto_add IS 'Boolean flag - if true, automatically create a transaction record when next_date arrives';
COMMENT ON COLUMN recurring_transactions.last_processed IS 'Timestamp of when this recurring transaction was last processed/executed';
COMMENT ON COLUMN recurring_transactions.extra_data IS 'JSON string for custom fields or additional metadata';
COMMENT ON COLUMN recurring_transactions.created_at IS 'Timestamp when this recurring transaction was created';
COMMENT ON COLUMN recurring_transactions.updated_at IS 'Timestamp when this recurring transaction was last modified';

-- ============================================================================
-- NOTIFICATIONS TABLE
-- ============================================================================

COMMENT ON TABLE notifications IS 'Notifications - smart alerts for financial events like budget limits, bill reminders, and unusual spending';

COMMENT ON COLUMN notifications.id IS 'Unique notification identifier (UUID format)';
COMMENT ON COLUMN notifications.user_id IS 'Foreign key to users table - identifies which user this notification is for (indexed)';
COMMENT ON COLUMN notifications.type IS 'Notification type: budget_alert, bill_reminder, goal_milestone, unusual_spending, low_balance, goal_completed, debt_paid_off';
COMMENT ON COLUMN notifications.title IS 'Short notification title displayed to user (e.g., "Budget Alert", "Bill Due Soon")';
COMMENT ON COLUMN notifications.message IS 'Full notification message with details';
COMMENT ON COLUMN notifications.status IS 'Status: unread (not yet viewed), read (user has viewed), dismissed (user dismissed)';
COMMENT ON COLUMN notifications.priority IS 'Priority level: 1=low (informational), 2=medium (worth attention), 3=high (urgent action needed)';
COMMENT ON COLUMN notifications.action_url IS 'Optional deep link to relevant screen in mobile app (e.g., /budgets/food, /bills/123)';
COMMENT ON COLUMN notifications.extra_data IS 'JSON string with context data for rendering the notification (amounts, dates, etc.)';
COMMENT ON COLUMN notifications.created_at IS 'Timestamp when this notification was created (indexed)';
COMMENT ON COLUMN notifications.read_at IS 'Timestamp when the user read this notification (null if unread)';

-- Migration complete!
-- Run: psql -d financial_planner -U postgres -f backend/migrations/003_add_schema_descriptions.sql
