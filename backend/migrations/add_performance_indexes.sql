-- Database Performance Optimization Migration
-- Date: 2025-11-05
-- Purpose: Add indexes for frequently queried columns to improve query performance

-- Add composite index on transactions for user_id + date queries
CREATE INDEX IF NOT EXISTS ix_transactions_user_date ON transactions(user_id, date);

-- Add composite index on transactions for user_id + type queries
CREATE INDEX IF NOT EXISTS ix_transactions_user_type ON transactions(user_id, type);

-- Add composite index on transactions for user_id + category queries
CREATE INDEX IF NOT EXISTS ix_transactions_user_category ON transactions(user_id, category);

-- Add index on transaction date for date range queries
CREATE INDEX IF NOT EXISTS ix_transactions_date ON transactions(date);

-- Add composite index on budgets for user_id + category lookups
CREATE INDEX IF NOT EXISTS ix_budgets_user_category ON budgets(user_id, category);

-- Analyze tables to update query planner statistics
ANALYZE transactions;
ANALYZE budgets;
ANALYZE debts_loans;
ANALYZE goals;

-- Display index information
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('transactions', 'budgets')
ORDER BY tablename, indexname;
