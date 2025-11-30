"""
SQLAlchemy Database Models
"""
from sqlalchemy import Column, String, Float, DateTime, Boolean, Text, Enum as SQLEnum, ForeignKey, Integer, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class User(Base):
    """User account"""
    __tablename__ = "users"
    __table_args__ = {'comment': 'User accounts - stores authentication and personal information for each user of the financial planning system'}

    id = Column(String, primary_key=True, comment='Unique user identifier (UUID format)')
    email = Column(String, unique=True, nullable=False, index=True, comment='User email address - used for login and notifications (unique, indexed)')
    password_hash = Column(String, nullable=False, comment='Hashed password for authentication - never store plain text passwords')
    name = Column(String, nullable=False, comment='User full name or display name')

    # Location & Localization (2025 standards)
    timezone = Column(String, default="UTC", comment='User timezone in IANA format (e.g., America/New_York, Asia/Kolkata) - used for date/time localization')
    currency = Column(String, default="USD", comment='User preferred currency code (e.g., USD, EUR, INR) - all financial amounts are displayed in this currency')
    country = Column(String, nullable=True, comment='User country code (e.g., US, IN, GB) - used for localization and regulations')

    created_at = Column(DateTime, default=datetime.utcnow, comment='Timestamp when the user account was created')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Timestamp when the user account was last modified')

    # Relationships
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    debts_loans = relationship("DebtLoan", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    logs = relationship("Log", back_populates="user", cascade="all, delete-orphan")
    insights = relationship("Insight", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    recurring_transactions = relationship("RecurringTransaction", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")


class TransactionType(str, enum.Enum):
    """Transaction types - case insensitive"""
    INCOME = "income"
    EXPENSE = "expense"
    LENDING = "lending"
    BORROWING = "borrowing"
    
    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive lookup"""
        if isinstance(value, str):
            value_lower = value.lower()
            for member in cls:
                if member.value == value_lower:
                    return member
        return None


class Transaction(Base):
    """Financial transaction"""
    __tablename__ = "transactions"
    __table_args__ = (
        Index('ix_transactions_user_date', 'user_id', 'date'),
        Index('ix_transactions_user_type', 'user_id', 'type'),
        Index('ix_transactions_user_category', 'user_id', 'category'),
        Index('ix_transactions_date', 'date'),
        {'comment': 'Financial transactions - records all income, expenses, lending, and borrowing activities for users'}
    )

    id = Column(String, primary_key=True, comment='Unique transaction identifier (UUID format)')
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True, comment='Foreign key to users table - identifies which user this transaction belongs to (indexed)')
    account_id = Column(String, ForeignKey("accounts.id"), nullable=True, index=True, comment='Optional foreign key to accounts table - links transaction to a specific bank account (indexed)')
    type = Column(SQLEnum(TransactionType, native_enum=False, create_constraint=False), nullable=False, comment='Transaction type: income (money earned), expense (money spent), lending (money lent to others), borrowing (money borrowed)')
    special_type = Column(String, nullable=True, comment='Special transaction type: default, upcoming (future bill), subscription (recurring), repetitive (regular pattern), credit (lent to others), debt (borrowed from others)')
    amount = Column(Float, nullable=False, comment='Transaction amount in the user currency - always positive, type determines if it increases or decreases net worth')
    description = Column(Text, nullable=False, comment='User-provided description of the transaction (e.g., "Groceries at Whole Foods", "Freelance payment")')
    category = Column(String, nullable=False, default="uncategorized", comment='Category for grouping transactions (e.g., food, transport, entertainment, salary) - used for spending analysis')
    category_id = Column(String, ForeignKey("categories.id"), nullable=True, comment='Optional foreign key to categories table for hierarchical category tracking')
    paired_transaction_id = Column(String, ForeignKey("transactions.id"), nullable=True, comment='For account transfers - links to the paired transaction (expense paired with income)')
    date = Column(DateTime, nullable=False, default=datetime.utcnow, comment='Date when the transaction occurred - can be different from created_at for backdated entries')
    recurring = Column(Boolean, default=False, comment='Boolean flag indicating if this is a recurring transaction (deprecated - use recurring_transactions table instead)')
    extra_data = Column(Text, comment='JSON string for storing additional custom fields or metadata')
    created_at = Column(DateTime, default=datetime.utcnow, comment='Timestamp when this transaction record was created in the system')

    # Relationships
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")


# ============================================================================
# ACCOUNT MANAGEMENT - Multi-Account Support
# ============================================================================


class AccountType(str, enum.Enum):
    """Account types following banking industry standards"""
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    INVESTMENT = "investment"
    CASH = "cash"
    OTHER = "other"

    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive lookup"""
        if isinstance(value, str):
            value_lower = value.lower()
            for member in cls:
                if member.value == value_lower:
                    return member
        return None


class AccountStatus(str, enum.Enum):
    """Account status"""
    ACTIVE = "active"
    CLOSED = "closed"
    FROZEN = "frozen"
    PENDING = "pending"

    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive lookup"""
        if isinstance(value, str):
            value_lower = value.lower()
            for member in cls:
                if member.value == value_lower:
                    return member
        return None


class Account(Base):
    """Bank accounts (checking, savings, credit cards, etc.)"""
    __tablename__ = "accounts"
    __table_args__ = {'comment': 'Bank accounts - tracks checking, savings, credit cards, investment accounts, and other financial accounts'}

    id = Column(String, primary_key=True, comment='Unique account identifier (UUID format)')
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True, comment='Foreign key to users table - identifies which user owns this account (indexed)')

    # Account Details
    account_type = Column(SQLEnum(AccountType, native_enum=False, create_constraint=False), nullable=False, comment='Type of account: checking, savings, credit_card, investment, cash, or other')
    account_name = Column(String, nullable=False, comment='User-friendly name for the account (e.g., "Chase Checking", "Emergency Savings Fund")')
    institution_name = Column(String, nullable=True, comment='Name of the bank or financial institution (e.g., "Chase Bank", "Wells Fargo")')
    account_number_last4 = Column(String, nullable=True, comment='Last 4 digits of account number for identification - stored for security (never store full account numbers)')

    # Financial Data
    current_balance = Column(Float, default=0.0, comment='Current account balance in user currency - updated when transactions are added or account is synced')
    currency = Column(String, default="USD", comment='Currency code for this account (e.g., USD, EUR) - may differ from user default currency')

    # Account Status & Metadata
    status = Column(SQLEnum(AccountStatus, native_enum=False, create_constraint=False), default=AccountStatus.ACTIVE, comment='Account status: active (currently in use), closed (no longer active), frozen (temporarily suspended), pending (awaiting activation)')
    opening_date = Column(DateTime, nullable=True, comment='Date when the account was opened at the financial institution')
    closing_date = Column(DateTime, nullable=True, comment='Date when the account was closed (null if still active)')
    interest_rate = Column(Float, nullable=True, comment='Annual interest rate as decimal (e.g., 0.025 for 2.5%) - applicable for savings accounts')

    # Additional Data
    notes = Column(Text, nullable=True, comment='User notes or additional information about this account')
    extra_data = Column(Text, comment='JSON string for storing custom fields or additional metadata')

    created_at = Column(DateTime, default=datetime.utcnow, comment='Timestamp when this account was added to the system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Timestamp when this account was last modified')

    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    credit_card_details = relationship("CreditCard", back_populates="account", uselist=False, cascade="all, delete-orphan")


class CardNetwork(str, enum.Enum):
    """Credit card network/issuer"""
    VISA = "visa"
    MASTERCARD = "mastercard"
    AMERICAN_EXPRESS = "american_express"
    DISCOVER = "discover"
    DINERS_CLUB = "diners_club"
    JCB = "jcb"
    UNIONPAY = "unionpay"
    OTHER = "other"

    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive lookup"""
        if isinstance(value, str):
            value_lower = value.lower()
            for member in cls:
                if member.value == value_lower:
                    return member
        return None


class CreditCard(Base):
    """Credit card specific details - extends Account model

    Industry standard credit card fields following best practices
    for personal finance management applications.
    """
    __tablename__ = "credit_cards"
    __table_args__ = {'comment': 'Credit card details - extends accounts table with credit-card-specific fields like credit limit, APR, payment dates, and rewards'}

    id = Column(String, primary_key=True, comment='Unique credit card record identifier (UUID format)')
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False, unique=True, index=True, comment='Foreign key to accounts table - links to the parent credit card account (unique, indexed)')

    # Credit Card Specific Fields
    credit_limit = Column(Float, nullable=False, comment='Total credit limit available on this card')
    available_credit = Column(Float, nullable=False, comment='Currently available credit (credit_limit minus current balance)')

    # APR & Fees (Industry Standard)
    apr = Column(Float, nullable=True, comment='Annual Percentage Rate - interest rate charged on unpaid balances (as decimal, e.g., 0.1999 for 19.99%)')
    annual_fee = Column(Float, default=0.0, comment='Yearly fee charged for having this credit card')
    late_fee = Column(Float, default=0.0, comment='Fee charged when payment is late')
    foreign_transaction_fee_percent = Column(Float, default=0.0, comment='Fee percentage charged on foreign currency transactions (e.g., 0.03 for 3%)')

    # Statement & Payment Info
    statement_balance = Column(Float, default=0.0, comment='Balance shown on the most recent statement')
    minimum_payment = Column(Float, default=0.0, comment='Minimum payment amount due for the current billing cycle')
    statement_date = Column(DateTime, nullable=True, comment='Date when the statement is generated each billing cycle')
    payment_due_date = Column(DateTime, nullable=True, index=True, comment='Date when payment is due - used for bill reminders (indexed for efficient querying of upcoming due dates)')
    last_payment_date = Column(DateTime, nullable=True, comment='Date of the most recent payment made')
    last_payment_amount = Column(Float, default=0.0, comment='Amount of the most recent payment')

    # Card Details
    card_network = Column(SQLEnum(CardNetwork, native_enum=False, create_constraint=False), nullable=True, comment='Card network/issuer: visa, mastercard, american_express, discover, diners_club, jcb, unionpay, other')
    card_last4 = Column(String, nullable=True, comment='Last 4 digits of the credit card number for identification')
    cardholder_name = Column(String, nullable=True, comment='Name printed on the credit card')
    expiration_month = Column(Integer, nullable=True, comment='Card expiration month (1-12)')
    expiration_year = Column(Integer, nullable=True, comment='Card expiration year (4-digit format, e.g., 2027)')

    # Rewards & Benefits
    rewards_program = Column(String, nullable=True, comment='Type of rewards program (e.g., "Cash Back", "Points", "Miles")')
    rewards_balance = Column(Float, default=0.0, comment='Current rewards balance - points, miles, or cash back amount accumulated')
    cashback_rate = Column(Float, nullable=True, comment='Cash back rate as decimal (e.g., 0.015 for 1.5% cash back)')

    # Grace Period & Credit Features
    grace_period_days = Column(Integer, default=21, comment='Number of days before interest is charged on new purchases (typically 21-25 days)')
    credit_utilization = Column(Float, default=0.0, comment='Credit utilization percentage - calculated as (balance / credit_limit) * 100 - important for credit score')

    # Alerts & Preferences
    alert_before_due_days = Column(Integer, default=3, comment='Number of days before due date to send payment reminder (default 3 days)')
    autopay_enabled = Column(Boolean, default=False, comment='Whether automatic payments are enabled for this card')
    autopay_amount = Column(String, default="minimum", comment='Autopay setting: minimum (pay minimum), statement_balance (pay full statement), full_balance (pay entire balance), custom (fixed amount)')

    # Additional Data
    extra_data = Column(Text, comment='JSON string for custom fields and additional metadata')

    created_at = Column(DateTime, default=datetime.utcnow, comment='Timestamp when this credit card record was created')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Timestamp when this credit card record was last modified')

    # Relationships
    account = relationship("Account", back_populates="credit_card_details")


class DebtLoanType(str, enum.Enum):
    """Debt/Loan types"""
    DEBT = "debt"
    LOAN = "loan"
    
    @classmethod
    def _missing_(cls, value):
        """Make enum case-insensitive"""
        if isinstance(value, str):
            value = value.lower()
            for member in cls:
                if member.value == value:
                    return member
        return None


class DebtLoanStatus(str, enum.Enum):
    """Status of debt/loan"""
    ACTIVE = "active"
    PAID_OFF = "paid_off"
    DEFAULTED = "defaulted"
    
    @classmethod
    def _missing_(cls, value):
        """Make enum case-insensitive"""
        if isinstance(value, str):
            value = value.lower()
            for member in cls:
                if member.value == value:
                    return member
        return None


class DebtLoan(Base):
    """Debt and loan tracking"""
    __tablename__ = "debts_loans"
    __table_args__ = {'comment': 'Debts and loans - tracks money owed (debts) and money lent to others (loans) with interest rates and payment schedules'}

    id = Column(String, primary_key=True, comment='Unique debt/loan identifier (UUID format)')
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True, comment='Foreign key to users table - identifies which user this debt/loan belongs to (indexed)')
    type = Column(SQLEnum(DebtLoanType, native_enum=False, create_constraint=False), nullable=False, comment='Type: debt (money user owes to others), loan (money user lent to others)')
    name = Column(String, nullable=False, comment='Name or description of the debt/loan (e.g., "Student Loan", "Credit Card Debt", "Loan to John")')
    principal_amount = Column(Float, nullable=False, comment='Original amount borrowed or lent')
    remaining_amount = Column(Float, nullable=False, comment='Current outstanding balance - decreases as payments are made')
    interest_rate = Column(Float, nullable=False, comment='Annual interest rate as percentage (e.g., 5.5 for 5.5% APR)')
    start_date = Column(DateTime, nullable=False, comment='Date when the debt/loan was initiated')
    monthly_payment = Column(Float, nullable=False, comment='Regular monthly payment amount')
    status = Column(SQLEnum(DebtLoanStatus, native_enum=False, create_constraint=False), default=DebtLoanStatus.ACTIVE, comment='Status: active (currently being paid), paid_off (fully paid), defaulted (failed to pay)')
    extra_data = Column(Text, comment='JSON string for repayment schedule, additional terms, or custom metadata')
    created_at = Column(DateTime, default=datetime.utcnow, comment='Timestamp when this debt/loan record was created')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Timestamp when this debt/loan record was last modified')

    # Relationships
    user = relationship("User", back_populates="debts_loans")


class GoalStatus(str, enum.Enum):
    """Goal status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    
    @classmethod
    def _missing_(cls, value):
        """Make enum case-insensitive"""
        if isinstance(value, str):
            value = value.lower()
            for member in cls:
                if member.value == value:
                    return member
        return None


class Goal(Base):
    """Financial goal"""
    __tablename__ = "goals"
    __table_args__ = {'comment': 'Financial goals - tracks savings targets like emergency funds, vacations, down payments, or other financial objectives'}

    id = Column(String, primary_key=True, comment='Unique goal identifier (UUID format)')
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True, comment='Foreign key to users table - identifies which user this goal belongs to (indexed)')
    name = Column(String, nullable=False, comment='Goal name or description (e.g., "Emergency Fund", "Vacation to Japan", "Down Payment")')
    target_amount = Column(Float, nullable=False, comment='Target amount to save for this goal')
    current_amount = Column(Float, default=0.0, comment='Amount saved so far towards this goal - updated manually or automatically')
    target_date = Column(DateTime, nullable=False, comment='Target date to achieve this goal')
    status = Column(SQLEnum(GoalStatus, native_enum=False, create_constraint=False), default=GoalStatus.ACTIVE, comment='Status: active (currently working towards), completed (goal achieved), abandoned (user stopped pursuing)')
    priority = Column(Integer, default=1, comment='Priority level for this goal (1=lowest, higher numbers=higher priority) - used for ranking multiple goals')
    extra_data = Column(Text, comment='JSON string for custom fields or additional metadata')
    created_at = Column(DateTime, default=datetime.utcnow, comment='Timestamp when this goal was created')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Timestamp when this goal was last modified')

    # Relationships
    user = relationship("User", back_populates="goals")


class Log(Base):
    """Activity log"""
    __tablename__ = "logs"
    __table_args__ = {'comment': 'Activity logs - audit trail of user actions and system events for security and debugging'}

    id = Column(String, primary_key=True, comment='Unique log entry identifier (UUID format)')
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True, comment='Foreign key to users table - identifies which user performed the action (indexed)')
    action = Column(String, nullable=False, comment='Action performed (e.g., "login", "add_transaction", "update_goal", "delete_account")')
    details = Column(Text, comment='JSON string with detailed information about the action including parameters and results')
    category = Column(String, default="general", comment='Log category for filtering (e.g., "auth", "transaction", "goal", "general")')
    ip_address = Column(String, comment='IP address from which the action was performed - for security auditing')
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment='Timestamp when the action was performed (indexed for efficient time-based queries)')

    # Relationships
    user = relationship("User", back_populates="logs")


class InsightType(str, enum.Enum):
    """Insight types"""
    DEBT = "debt"
    SAVINGS = "savings"
    SPENDING = "spending"
    GOAL = "goal"
    GENERAL = "general"
    
    @classmethod
    def _missing_(cls, value):
        """Make enum case-insensitive"""
        if isinstance(value, str):
            value = value.lower()
            for member in cls:
                if member.value == value:
                    return member
        return None


class Insight(Base):
    """AI-generated insights"""
    __tablename__ = "insights"
    __table_args__ = {'comment': 'AI-generated insights - personalized financial recommendations and observations generated by the AI agent'}

    id = Column(String, primary_key=True, comment='Unique insight identifier (UUID format)')
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True, comment='Foreign key to users table - identifies which user this insight is for (indexed)')
    type = Column(SQLEnum(InsightType, native_enum=False, create_constraint=False), nullable=False, comment='Insight type: debt (debt-related advice), savings (savings recommendations), spending (spending patterns), goal (goal progress), general (other insights)')
    message = Column(Text, nullable=False, comment='The insight message text - explains the observation or recommendation to the user')
    priority = Column(Integer, default=1, comment='Priority level (1=low, 2=medium, 3=high) - higher priority insights shown first')
    is_read = Column(Boolean, default=False, comment='Boolean flag indicating if the user has read this insight')
    extra_data = Column(Text, comment='JSON string with supporting data, calculations, or additional context')
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment='Timestamp when this insight was generated (indexed)')

    # Relationships
    user = relationship("User", back_populates="insights")


# ============================================================================
# TIER 1 CRITICAL FEATURES (2025)
# ============================================================================


class Budget(Base):
    """Monthly budget by category"""
    __tablename__ = "budgets"
    __table_args__ = (
        Index('ix_budgets_user_category', 'user_id', 'category'),
        {'comment': 'Budgets - spending limits by category for monthly, weekly, or yearly periods'}
    )

    id = Column(String, primary_key=True, comment='Unique budget identifier (UUID format)')
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True, comment='Foreign key to users table - identifies which user this budget belongs to (indexed)')
    category = Column(String, nullable=False, index=True, comment='Category this budget applies to (e.g., food, transport, entertainment) - must match transaction categories (indexed)')
    amount = Column(Float, nullable=False, comment='Budget limit amount for this category in the specified period')
    period = Column(String, default="monthly", comment='Budget period: monthly (most common), weekly, or yearly')
    start_date = Column(DateTime, nullable=False, comment='Date when this budget becomes effective')
    end_date = Column(DateTime, nullable=True, comment='Date when this budget expires (null means ongoing/indefinite)')
    is_active = Column(Boolean, default=True, comment='Boolean flag indicating if this budget is currently active')
    alert_threshold = Column(Float, default=0.9, comment='Percentage of budget at which to send alert (e.g., 0.9 for 90%) - triggers notification when spending reaches this level')
    extra_data = Column(Text, comment='JSON string for custom fields or additional metadata')
    created_at = Column(DateTime, default=datetime.utcnow, comment='Timestamp when this budget was created')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Timestamp when this budget was last modified')

    # Relationships
    user = relationship("User", back_populates="budgets")


class RecurrenceFrequency(str, enum.Enum):
    """Recurrence frequency options - case insensitive"""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    
    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive lookup"""
        if isinstance(value, str):
            value_lower = value.lower()
            for member in cls:
                if member.value == value_lower:
                    return member
        return None
    
    def __str__(self):
        """Return the lowercase value for database storage"""
        return self.value


class RecurringTransaction(Base):
    """Scheduled recurring transactions and bills"""
    __tablename__ = "recurring_transactions"
    __table_args__ = {'comment': 'Recurring transactions - scheduled bills, subscriptions, and regular income like salary'}

    id = Column(String, primary_key=True, comment='Unique recurring transaction identifier (UUID format)')
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True, comment='Foreign key to users table - identifies which user this recurring transaction belongs to (indexed)')
    type = Column(SQLEnum(TransactionType, native_enum=False, create_constraint=False, values_callable=lambda x: [e.value for e in x]), nullable=False, comment='Transaction type: income (recurring earnings like salary), expense (recurring bills like rent), lending, or borrowing')
    amount = Column(Float, nullable=False, comment='Amount for each occurrence of this recurring transaction')
    description = Column(Text, nullable=False, comment='Description (e.g., "Netflix Subscription", "Monthly Salary", "Rent Payment")')
    category = Column(String, nullable=False, comment='Category for this recurring transaction - used for budgeting and analysis')
    frequency = Column(SQLEnum(RecurrenceFrequency, native_enum=False, create_constraint=False, values_callable=lambda x: [e.value for e in x]), nullable=False, comment='How often this transaction occurs: daily, weekly, biweekly, monthly, quarterly, or yearly')
    next_date = Column(DateTime, nullable=False, index=True, comment='Next scheduled date for this transaction - updated after each occurrence (indexed for efficient scheduling queries)')
    end_date = Column(DateTime, nullable=True, comment='Date when this recurring transaction stops (null means indefinite)')
    is_active = Column(Boolean, default=True, comment='Boolean flag indicating if this recurring transaction is currently active')
    remind_days_before = Column(Integer, default=3, comment='Number of days before the transaction to send a reminder notification (default 3 days)')
    auto_add = Column(Boolean, default=True, comment='Boolean flag - if true, automatically create a transaction record when next_date arrives')
    last_processed = Column(DateTime, nullable=True, comment='Timestamp of when this recurring transaction was last processed/executed')
    extra_data = Column(Text, comment='JSON string for custom fields or additional metadata')
    created_at = Column(DateTime, default=datetime.utcnow, comment='Timestamp when this recurring transaction was created')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Timestamp when this recurring transaction was last modified')

    # Relationships
    user = relationship("User", back_populates="recurring_transactions")


class NotificationType(str, enum.Enum):
    """Notification types"""
    BUDGET_ALERT = "budget_alert"
    BILL_REMINDER = "bill_reminder"
    GOAL_MILESTONE = "goal_milestone"
    UNUSUAL_SPENDING = "unusual_spending"
    LOW_BALANCE = "low_balance"
    GOAL_COMPLETED = "goal_completed"
    DEBT_PAID_OFF = "debt_paid_off"
    
    @classmethod
    def _missing_(cls, value):
        """Make enum case-insensitive"""
        if isinstance(value, str):
            value = value.lower()
            for member in cls:
                if member.value == value:
                    return member
        return None


class NotificationStatus(str, enum.Enum):
    """Notification status"""
    UNREAD = "unread"
    READ = "read"
    DISMISSED = "dismissed"
    
    @classmethod
    def _missing_(cls, value):
        """Make enum case-insensitive"""
        if isinstance(value, str):
            value = value.lower()
            for member in cls:
                if member.value == value:
                    return member
        return None


class Notification(Base):
    """Smart notifications for financial events"""
    __tablename__ = "notifications"
    __table_args__ = {'comment': 'Notifications - smart alerts for financial events like budget limits, bill reminders, and unusual spending'}

    id = Column(String, primary_key=True, comment='Unique notification identifier (UUID format)')
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True, comment='Foreign key to users table - identifies which user this notification is for (indexed)')
    type = Column(SQLEnum(NotificationType, native_enum=False, create_constraint=False), nullable=False, comment='Notification type: budget_alert, bill_reminder, goal_milestone, unusual_spending, low_balance, goal_completed, debt_paid_off')
    title = Column(String, nullable=False, comment='Short notification title displayed to user (e.g., "Budget Alert", "Bill Due Soon")')
    message = Column(Text, nullable=False, comment='Full notification message with details')
    status = Column(SQLEnum(NotificationStatus, native_enum=False, create_constraint=False), default=NotificationStatus.UNREAD, comment='Status: unread (not yet viewed), read (user has viewed), dismissed (user dismissed)')
    priority = Column(Integer, default=1, comment='Priority level: 1=low (informational), 2=medium (worth attention), 3=high (urgent action needed)')
    action_url = Column(String, nullable=True, comment='Optional deep link to relevant screen in mobile app (e.g., /budgets/food, /bills/123)')
    extra_data = Column(Text, comment='JSON string with context data for rendering the notification (amounts, dates, etc.)')
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment='Timestamp when this notification was created (indexed)')
    read_at = Column(DateTime, nullable=True, comment='Timestamp when the user read this notification (null if unread)')

    # Relationships
    user = relationship("User", back_populates="notifications")


class Category(Base):
    """User-specific transaction categories"""
    __tablename__ = "categories"
    __table_args__ = (
        Index('ix_categories_user_name', 'user_id', 'name', unique=True),
        {'comment': 'User-specific categories - personalized category system that learns and adapts to each user'}
    )

    id = Column(String, primary_key=True, comment='Unique category identifier (UUID format)')
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True, comment='Foreign key to users table - identifies which user this category belongs to (indexed)')
    name = Column(String, nullable=False, comment='Category name (e.g., "groceries", "streaming", "gas") - lowercase, snake_case format')
    display_name = Column(String, nullable=False, comment='Human-readable display name (e.g., "Groceries", "Streaming Services", "Gas & Fuel")')
    parent_category = Column(String, nullable=True, comment='Parent category for hierarchical organization (e.g., "groceries" parent is "food")')
    icon = Column(String, nullable=True, comment='Icon identifier for UI display (e.g., "shopping-cart", "film", "car")')
    color = Column(String, nullable=True, comment='Color hex code for UI display (e.g., "#4CAF50")')
    
    # AI Learning Metadata
    usage_count = Column(Integer, default=0, comment='Number of times this category has been used - helps AI prioritize common categories')
    ai_suggested = Column(Boolean, default=False, comment='Boolean flag - true if this category was suggested by AI, false if user-created or default')
    keywords = Column(Text, nullable=True, comment='JSON array of keywords associated with this category for matching (e.g., ["whole foods", "trader joes", "safeway"])')
    
    # Status
    is_active = Column(Boolean, default=True, comment='Boolean flag indicating if this category is currently active and available for use')
    is_default = Column(Boolean, default=False, comment='Boolean flag - true for system default categories that were seeded on user creation')
    
    created_at = Column(DateTime, default=datetime.utcnow, comment='Timestamp when this category was created')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Timestamp when this category was last modified')

    # Relationships
    user = relationship("User", back_populates="categories")
