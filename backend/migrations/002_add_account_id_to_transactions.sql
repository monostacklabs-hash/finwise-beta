-- Add account_id column to transactions table
-- This links transactions to specific accounts for multi-account support

ALTER TABLE transactions 
ADD COLUMN IF NOT EXISTS account_id VARCHAR(36) REFERENCES accounts(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id);

-- Migration complete!
-- This allows transactions to be optionally linked to specific accounts
