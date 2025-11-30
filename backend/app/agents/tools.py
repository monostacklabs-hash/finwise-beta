"""
LangGraph Financial Tools - 2025 Industry Standard
These tools allow the AI agent to autonomously interact with the financial system
"""
from langchain_core.tools import tool, StructuredTool
from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Annotated, Literal, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, case
import uuid
import logging

logger = logging.getLogger(__name__)

from ..database.models import (
    Transaction, DebtLoan, Goal, Insight, Log,
    TransactionType, DebtLoanType, DebtLoanStatus, GoalStatus, InsightType,
    Budget, RecurringTransaction, RecurrenceFrequency, Notification, NotificationStatus,
    Account, CreditCard, AccountType, AccountStatus, CardNetwork
)
from ..services.health_calculator import HealthCalculator
from ..services.debt_optimizer import DebtOptimizer
from ..services.goal_projector import GoalProjector
from ..services.transaction_categorizer import TransactionCategorizer
from ..services.ai_transaction_categorizer import AITransactionCategorizer
from ..services.budget_tracker import BudgetTracker
from ..services.cashflow_forecaster import CashFlowForecaster
from ..services.recurring_scheduler import RecurringScheduler
from ..services.recurring_detector import RecurringDetector


# Context holder for database session, user ID, and currency
class ToolContext:
    db: Session = None
    user_id: str = None
    currency: str = "USD"  # User's preferred currency
    currency_symbol: str = "$"  # Currency symbol for display


# Pydantic schemas for strict type validation
class AddTransactionInput(BaseModel):
    """Input schema for add_transaction tool - Groq compatible"""
    amount: float = Field(description="Transaction amount")
    description: str = Field(description="Transaction description")
    transaction_type: str = Field(description="Type: income, expense, lending, or borrowing")
    category: str = Field(default="auto", description="Category - use 'auto' to auto-categorize")
    date: str = Field(default="today", description="Date in YYYY-MM-DD format - use 'today' for current date")

    @field_validator('amount', mode='before')
    @classmethod
    def coerce_amount_to_float(cls, v):
        """Convert string to float if needed (Groq compatibility)"""
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"Invalid amount: {v}")
        return v


class GetTransactionsInput(BaseModel):
    """Input schema for get_transactions tool - Groq compatible"""
    model_config = {"str_strip_whitespace": True, "coerce_numbers_to_str": False}

    limit: int = Field(default=10, description="Number of recent transactions to retrieve")
    transaction_type: str = Field(default="all", description="Filter by type: income, expense, lending, borrowing, or 'all' for no filter")

    @field_validator('limit', mode='before')
    @classmethod
    def coerce_limit_to_int(cls, v):
        """Convert string to int if needed (Groq compatibility)"""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return 10  # Default fallback
        return v


class AddDebtLoanInput(BaseModel):
    """Input schema for add_debt_or_loan tool - Groq compatible"""
    name: str = Field(description="Name/description of the debt or loan")
    amount: float = Field(description="Principal amount")
    interest_rate: float = Field(description="Annual interest rate as percentage (e.g., 5.5 for 5.5%)")
    monthly_payment: float = Field(description="Monthly payment amount")
    debt_type: str = Field(description="Type: debt or loan")
    start_date: str = Field(default="today", description="Start date in YYYY-MM-DD format - use 'today' for current date")

    @field_validator('amount', 'interest_rate', 'monthly_payment', mode='before')
    @classmethod
    def coerce_numbers_to_float(cls, v):
        """Convert string to float if needed (Groq compatibility)"""
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"Invalid number: {v}")
        return v


class OptimizeDebtInput(BaseModel):
    """Input schema for optimize_debt_repayment tool - Groq compatible"""
    extra_monthly_budget: float = Field(description="Extra monthly amount available for debt repayment")

    @field_validator('extra_monthly_budget', mode='before')
    @classmethod
    def coerce_budget_to_float(cls, v):
        """Convert string to float if needed (Groq compatibility)"""
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"Invalid budget amount: {v}")
        return v


class AddGoalInput(BaseModel):
    """Input schema for add_financial_goal tool - Groq compatible"""
    name: str = Field(description="Goal name/description")
    target_amount: float = Field(description="Target amount to save")
    target_date: str = Field(description="Target date in YYYY-MM-DD format")
    current_amount: float = Field(default=0.0, description="Current saved amount (optional)")

    @field_validator('target_amount', 'current_amount', mode='before')
    @classmethod
    def coerce_amounts_to_float(cls, v):
        """Convert string to float if needed (Groq compatibility)"""
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"Invalid amount: {v}")
        return v


class ProjectGoalInput(BaseModel):
    goal_name: str = Field(description="Name of the goal to project")


# ============================================================================
# TIER 1 FEATURE - Budget Management Input Schemas
# ============================================================================

class CreateBudgetInput(BaseModel):
    """Input schema for create_budget tool"""
    category: str = Field(description="Budget category (e.g., food, transport, entertainment)")
    amount: float = Field(description="Budget amount for the period")
    period: str = Field(default="monthly", description="Budget period: monthly, weekly, or yearly")
    alert_threshold: float = Field(default=0.9, description="Alert when this percentage is reached (e.g., 0.9 for 90%)")

    @field_validator('amount', mode='before')
    @classmethod
    def coerce_amount_to_float(cls, v):
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"Invalid amount: {v}")
        return v


class CreateRecurringInput(BaseModel):
    """Input schema for create_recurring_transaction tool"""
    transaction_type: str = Field(description="Type: income or expense")
    amount: float = Field(description="Transaction amount")
    description: str = Field(description="Description (e.g., 'Netflix subscription', 'Salary')")
    category: str = Field(description="Category")
    frequency: str = Field(description="Frequency: daily, weekly, biweekly, monthly, quarterly, or yearly")
    next_date: str = Field(description="Next occurrence date in YYYY-MM-DD format")
    auto_add: bool = Field(default=True, description="Automatically add transactions on schedule")

    @field_validator('amount', mode='before')
    @classmethod
    def coerce_amount_to_float(cls, v):
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"Invalid amount: {v}")
        return v


class CashFlowForecastInput(BaseModel):
    """Input schema for get_cashflow_forecast tool"""
    starting_balance: float = Field(description="Current account balance")
    forecast_days: int = Field(default=90, description="Number of days to forecast (default 90)")

    @field_validator('starting_balance', mode='before')
    @classmethod
    def coerce_balance_to_float(cls, v):
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"Invalid balance: {v}")
        return v

    @field_validator('forecast_days', mode='before')
    @classmethod
    def coerce_days_to_int(cls, v):
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return 90
        return v


# ============================================================================
# Account Management Input Schemas
# ============================================================================


class AddAccountInput(BaseModel):
    """Input schema for add_account tool"""
    account_type: str = Field(description="Account type: checking, savings, credit_card, investment, cash, or other")
    account_name: str = Field(description="Account name/nickname (e.g., 'Chase Checking', 'Emergency Savings')")
    institution_name: str = Field(default="", description="Bank or institution name")
    current_balance: float = Field(default=0.0, description="Current account balance")
    account_number_last4: str = Field(default="", description="Last 4 digits of account number")

    @field_validator('current_balance', mode='before')
    @classmethod
    def coerce_balance_to_float(cls, v):
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"Invalid balance: {v}")
        return v


class AddCreditCardInput(BaseModel):
    """Input schema for add_credit_card tool"""
    account_id: str = Field(description="Account ID (from add_account)")
    credit_limit: float = Field(description="Total credit limit")
    available_credit: float = Field(description="Currently available credit")
    apr: float = Field(default=0.0, description="Annual Percentage Rate (APR)")
    minimum_payment: float = Field(default=0.0, description="Minimum payment amount")
    payment_due_date: str = Field(default="", description="Payment due date in YYYY-MM-DD format")
    card_network: str = Field(default="", description="Card network: visa, mastercard, american_express, discover, etc.")

    @field_validator('credit_limit', 'available_credit', 'apr', 'minimum_payment', mode='before')
    @classmethod
    def coerce_numbers_to_float(cls, v):
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"Invalid number: {v}")
        return v


from ..database.exceptions import DatabaseOperationError, InvalidInputError, handle_sqlalchemy_error
from ..database.session import db_transaction
from sqlalchemy.exc import SQLAlchemyError

def _add_transaction(
    amount: float,
    description: str,
    transaction_type: str,
    category: str = "auto",
    date: str = "today",
) -> Dict:
    """
    Add a financial transaction (income, expense, lending, or borrowing).
    Use this when the user wants to record any financial activity.

    Returns:
        Dict: A structured dictionary with transaction details and metadata
    """
    db = ToolContext.db
    user_id = ToolContext.user_id

    # Validate inputs
    if amount <= 0:
        raise InvalidInputError(
            field="amount",
            value=amount,
            reason="Transaction amount must be positive"
        )

    # Validate transaction type
    try:
        transaction_type_enum = TransactionType(transaction_type.lower())
    except ValueError:
        raise InvalidInputError(
            field="transaction_type",
            value=transaction_type,
            reason="Invalid transaction type"
        )

    # Parse date
    try:
        trans_date = datetime.fromisoformat(date) if date and date != "today" else datetime.utcnow()
    except ValueError:
        raise InvalidInputError(
            field="date",
            value=date,
            reason="Invalid date format. Use YYYY-MM-DD or 'today'"
        )

    # Auto-categorize if not provided or set to 'auto'
    if not category or category == "auto":
        try:
            categorization = AITransactionCategorizer.categorize(
                description=description,
                amount=amount,
                trans_type=transaction_type,
                user_id=user_id,
                db=db,
                use_ai=True,
            )
            category = categorization["category"]

            # Log categorization details for debugging
            logger.info(
                f"Categorized '{description}' as '{category}' "
                f"(confidence: {categorization.get('confidence', 0):.2f}, "
                f"method: {categorization.get('method', 'unknown')})"
            )
        except Exception as e:
            logger.warning(f"AI Categorization failed: {e}. Using default category.")
            category = "uncategorized"

    # Create transaction with robust error handling
    try:
        with db_transaction(db) as session:
            transaction = Transaction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                type=transaction_type_enum,
                amount=amount,
                description=description,
                category=category,
                date=trans_date
            )
            session.add(transaction)

        return {
            "success": True,
            "transaction_id": transaction.id,
            "amount": amount,
            "description": description,
            "category": category,
            "date": trans_date.isoformat(),
            "message": "Transaction added successfully"
        }
    except SQLAlchemyError as e:
        handle_sqlalchemy_error(e, "add_transaction")  # Raises a custom DatabaseOperationError
        db.flush()  # Flush to catch errors before commit
        db.commit()

        return f"✅ Transaction added successfully: {ToolContext.currency_symbol}{amount} {transaction_type} in {category} category"

    except Exception as e:
        db.rollback()  # Rollback on error to clean up session
        return f"❌ Error adding transaction: {str(e)}"


def _get_transactions(
    limit: int = 10,
    transaction_type: str = "all",
) -> str:
    """
    Retrieve recent transactions for the user.
    Use this to show the user their transaction history or analyze spending patterns.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        query = db.query(Transaction).filter(Transaction.user_id == user_id)

        if transaction_type and transaction_type != "all":
            query = query.filter(Transaction.type == TransactionType(transaction_type.lower()))

        transactions = query.order_by(Transaction.date.desc()).limit(limit).all()

        if not transactions:
            return "No transactions found."

        result = f"Found {len(transactions)} transaction(s):\n\n"
        for t in transactions:
            result += f"• {t.date.strftime('%Y-%m-%d')}: {ToolContext.currency_symbol}{t.amount} - {t.description} ({t.type.value}, {t.category})\n"

        return result

    except Exception as e:
        return f"❌ Error retrieving transactions: {str(e)}"


@tool
def calculate_financial_health() -> str:
    """
    Calculate comprehensive financial health metrics including net worth, savings rate,
    debt ratio, liquidity ratio, and overall health score.
    Use this when the user asks about their financial health or overview.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        # Use SQL aggregations for better performance
        total_income = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.INCOME
        ).scalar() or 0.0

        total_expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE
        ).scalar() or 0.0

        # Get total debt using SQL aggregation
        total_debt = db.query(func.sum(DebtLoan.remaining_amount)).filter(
            DebtLoan.user_id == user_id,
            DebtLoan.status == DebtLoanStatus.ACTIVE
        ).scalar() or 0.0

        # Check for recurring transactions if no actual transactions exist
        recurring_info = ""
        if total_income == 0 and total_expenses == 0:
            recurring_income = db.query(func.sum(RecurringTransaction.amount)).filter(
                RecurringTransaction.user_id == user_id,
                RecurringTransaction.type == "income",
                RecurringTransaction.is_active == True
            ).scalar() or 0.0
            
            recurring_expenses = db.query(func.sum(RecurringTransaction.amount)).filter(
                RecurringTransaction.user_id == user_id,
                RecurringTransaction.type == "expense",
                RecurringTransaction.is_active == True
            ).scalar() or 0.0
            
            if recurring_income > 0 or recurring_expenses > 0:
                # Use recurring transactions for projection
                total_income = recurring_income
                total_expenses = recurring_expenses
                recurring_info = "\n\n⚠️ Note: Using recurring transaction data for projection (no actual transactions recorded yet)"

        # Calculate assets (simplified: income - expenses)
        total_assets = max(0, total_income - total_expenses)

        # Calculate health metrics
        health = HealthCalculator.calculate_health_metrics(
            total_income, total_expenses, total_debt, total_assets
        )

        # Format response
        health_category = HealthCalculator.categorize_health_score(health["health_score"])

        result = f"""📊 Financial Health Report:

💰 Net Worth: {ToolContext.currency_symbol}{health['net_worth']:,.2f}
📈 Health Score: {health['health_score']}/100 ({health_category})

Income & Expenses:
• Total Income: {ToolContext.currency_symbol}{health['total_income']:,.2f}
• Total Expenses: {ToolContext.currency_symbol}{health['total_expenses']:,.2f}
• Savings Rate: {health['savings_rate']:.1f}%

Assets & Debt:
• Total Assets: {ToolContext.currency_symbol}{health['total_assets']:,.2f}
• Total Debt: {ToolContext.currency_symbol}{health['total_debt']:,.2f}
• Debt Ratio: {health['debt_ratio']:.1f}%
• Liquidity Ratio: {health['liquidity_ratio']:.2f}{recurring_info}"""

        return result

    except Exception as e:
        return f"❌ Error calculating health: {str(e)}"


def _add_debt_or_loan(
    name: str,
    amount: float,
    interest_rate: float,
    monthly_payment: float,
    debt_type: str,
    start_date: str = "today",
) -> str:
    """
    Add a debt (money you owe) or loan (money you lent to someone).
    Use this when the user mentions credit cards, loans, mortgages, or lending money.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        start = datetime.fromisoformat(start_date) if start_date and start_date != "today" else datetime.utcnow()

        debt_loan = DebtLoan(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=DebtLoanType(debt_type),
            name=name,
            principal_amount=amount,
            remaining_amount=amount,
            interest_rate=interest_rate,
            start_date=start,
            monthly_payment=monthly_payment,
            status=DebtLoanStatus.ACTIVE,
        )

        db.add(debt_loan)
        db.flush()
        db.commit()

        return f"✅ {debt_type.capitalize()} added: {name} - {ToolContext.currency_symbol}{amount:,.2f} at {interest_rate}% interest"

    except Exception as e:
        db.rollback()
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error adding {debt_type}: {error_details}")
        return f"❌ Error adding {debt_type}: {str(e)}"


@tool
def get_debts_and_loans() -> str:
    """
    Retrieve all active debts and loans.
    Use this to show the user their current debts/loans or when analyzing debt situation.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        debts_loans = (
            db.query(DebtLoan)
            .filter(DebtLoan.user_id == user_id, DebtLoan.status == DebtLoanStatus.ACTIVE)
            .all()
        )

        if not debts_loans:
            return "✅ Great news! You have no active debts or loans."

        result = f"Found {len(debts_loans)} active debt(s)/loan(s):\n\n"

        total_debt = 0
        total_loans = 0

        for dl in debts_loans:
            result += f"• {dl.name}: {ToolContext.currency_symbol}{dl.remaining_amount:,.2f} remaining at {dl.interest_rate}% ({dl.type.value})\n"
            result += f"  Monthly payment: {ToolContext.currency_symbol}{dl.monthly_payment:,.2f}\n\n"

            if dl.type == DebtLoanType.DEBT:
                total_debt += dl.remaining_amount
            else:
                total_loans += dl.remaining_amount

        result += f"Total Debt: {ToolContext.currency_symbol}{total_debt:,.2f}\n"
        result += f"Total Loans Out: {ToolContext.currency_symbol}{total_loans:,.2f}"

        return result

    except Exception as e:
        return f"❌ Error retrieving debts/loans: {str(e)}"


def _optimize_debt_repayment(extra_monthly_budget: float) -> str:
    """
    Calculate optimal debt repayment strategy (avalanche vs snowball).
    Use this when the user asks how to pay off debt faster or wants debt advice.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        debts = (
            db.query(DebtLoan)
            .filter(
                DebtLoan.user_id == user_id,
                DebtLoan.type == DebtLoanType.DEBT,
                DebtLoan.status == DebtLoanStatus.ACTIVE,
            )
            .all()
        )

        if not debts:
            return "✅ You have no active debts. Great job!"

        # Convert to dict format for optimizer
        debt_list = [
            {
                "id": d.id,
                "name": d.name,
                "remainingAmount": d.remaining_amount,
                "interestRate": d.interest_rate,
                "monthlyPayment": d.monthly_payment,
            }
            for d in debts
        ]

        optimization = DebtOptimizer.optimize_debt_strategy(debt_list, extra_monthly_budget)

        result = f"""💡 Debt Repayment Strategy Recommendation:

Recommended: {optimization['recommended_strategy'].upper()} Method
{optimization['summary']}

Avalanche Method (Pay highest interest first):
• Total time: {optimization['avalanche']['total_months']} months
• Total interest: {ToolContext.currency_symbol}{optimization['avalanche']['total_interest']:,.2f}

Snowball Method (Pay smallest balance first):
• Total time: {optimization['snowball']['total_months']} months
• Total interest: {ToolContext.currency_symbol}{optimization['snowball']['total_interest']:,.2f}

With {ToolContext.currency_symbol}{extra_monthly_budget:,.2f} extra per month, you can save {ToolContext.currency_symbol}{optimization['interest_savings']:,.2f} by using the {optimization['recommended_strategy']} method."""

        return result

    except Exception as e:
        return f"❌ Error optimizing debt: {str(e)}"


def _add_financial_goal(
    name: str,
    target_amount: float,
    target_date: str,
    current_amount: float = 0.0,
) -> str:
    """
    Create a new financial goal (e.g., emergency fund, vacation, down payment).
    Use this when the user wants to set a savings goal or target.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        target = datetime.fromisoformat(target_date)

        goal = Goal(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            target_amount=target_amount,
            current_amount=current_amount,
            target_date=target,
            status=GoalStatus.ACTIVE,
        )

        db.add(goal)
        db.flush()
        db.commit()

        return f"✅ Goal created: {name} - Save {ToolContext.currency_symbol}{target_amount:,.2f} by {target_date}"

    except Exception as e:
        db.rollback()
        return f"❌ Error adding goal: {str(e)}"


@tool
def get_goals() -> str:
    """
    Retrieve all active financial goals.
    Use this to show the user their goals or when discussing goal progress.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        goals = (
            db.query(Goal)
            .filter(Goal.user_id == user_id, Goal.status == GoalStatus.ACTIVE)
            .all()
        )

        if not goals:
            return "You don't have any active goals yet. Would you like to create one?"

        result = f"You have {len(goals)} active goal(s):\n\n"

        for g in goals:
            progress = (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0
            result += f"• {g.name}:\n"
            result += f"  Target: {ToolContext.currency_symbol}{g.target_amount:,.2f} by {g.target_date.strftime('%Y-%m-%d')}\n"
            result += f"  Current: {ToolContext.currency_symbol}{g.current_amount:,.2f} ({progress:.1f}% complete)\n"
            result += f"  Remaining: {ToolContext.currency_symbol}{g.target_amount - g.current_amount:,.2f}\n\n"

        return result

    except Exception as e:
        return f"❌ Error retrieving goals: {str(e)}"


def _project_goal_achievement(goal_name: str) -> str:
    """
    Project when a goal will be achieved based on current income and expenses.
    Use this when the user asks "when will I reach my goal" or "can I afford this goal".
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        # Find the goal
        goal = (
            db.query(Goal)
            .filter(
                Goal.user_id == user_id,
                Goal.name.ilike(f"%{goal_name}%"),
                Goal.status == GoalStatus.ACTIVE,
            )
            .first()
        )

        if not goal:
            return f"❌ Goal '{goal_name}' not found. Use get_goals to see available goals."

        # Calculate monthly income and expenses using SQL aggregations
        total_income = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.INCOME
        ).scalar() or 0.0
        
        total_expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE
        ).scalar() or 0.0

        # Estimate monthly averages (simplified)
        monthly_income = total_income / 12 if total_income > 0 else 0
        monthly_expenses = total_expenses / 12 if total_expenses > 0 else 0

        projection = GoalProjector.calculate_goal_projection(
            goal.target_amount,
            goal.current_amount,
            goal.target_date,
            monthly_income,
            monthly_expenses,
        )

        status_emoji = {"achieved": "🎉", "on-track": "✅", "at-risk": "⚠️", "behind": "❌"}

        result = f"""{status_emoji.get(projection['status'], '📊')} Goal Projection: {goal.name}

Target: {ToolContext.currency_symbol}{projection['target_amount']:,.2f} by {projection['target_date']}
Current: {ToolContext.currency_symbol}{projection['current_amount']:,.2f}
Remaining: {ToolContext.currency_symbol}{projection['remaining_amount']:,.2f}

Timeline:
• Months remaining: {projection['months_remaining']}
• Monthly contribution needed: {ToolContext.currency_symbol}{projection['monthly_contribution_needed']:,.2f}
• Available monthly surplus: {ToolContext.currency_symbol}{projection['available_monthly']:,.2f}
• Estimated completion: {projection['estimated_completion']} ({projection['estimated_months']} months)

Status: {projection['status'].upper()}
Probability of on-time achievement: {projection['probability']*100:.0f}%"""

        return result

    except Exception as e:
        return f"❌ Error projecting goal: {str(e)}"


@tool
def analyze_spending_by_category() -> str:
    """
    Analyze spending patterns by category.
    Use this when the user asks "where is my money going" or wants spending breakdown.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        # Use SQL GROUP BY for efficient aggregation
        from sqlalchemy import case
        
        category_results = db.query(
            case(
                (Transaction.category == None, "uncategorized"),
                (Transaction.category == "", "uncategorized"),
                else_=Transaction.category
            ).label('category'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE
        ).group_by('category').all()

        if not category_results:
            return "No expenses recorded yet."

        # Calculate total
        total = sum(row.total for row in category_results)

        # Sort by amount
        sorted_categories = sorted(category_results, key=lambda x: x.total, reverse=True)

        result = f"💸 Spending Breakdown (Total: {ToolContext.currency_symbol}{total:,.2f}):\n\n"

        for row in sorted_categories:
            percentage = (row.total / total * 100) if total > 0 else 0
            result += f"• {row.category.title()}: {ToolContext.currency_symbol}{row.total:,.2f} ({percentage:.1f}%)\n"

        return result

    except Exception as e:
        return f"❌ Error analyzing spending: {str(e)}"


# ============================================================================
# TIER 1 FEATURE TOOLS - Budget Management
# ============================================================================

@tool
def get_budgets() -> str:
    """
    Get all active budgets with their current status (spent vs budgeted).
    Use this when the user asks about their budgets or wants to see budget status.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        budget_statuses = BudgetTracker.get_all_budget_statuses(db, user_id)

        if not budget_statuses:
            return "You don't have any active budgets yet. Would you like to create one?"

        result = f"📊 Active Budgets ({len(budget_statuses)}):\n\n"

        for budget in budget_statuses:
            status_emoji = "✅" if not budget["is_overspent"] else "❌"
            if budget["is_near_limit"] and not budget["is_overspent"]:
                status_emoji = "⚠️"

            result += f"{status_emoji} {budget['category'].title()} ({budget['period']})\n"
            result += f"  Budget: {ToolContext.currency_symbol}{budget['budgeted_amount']:,.2f}\n"
            result += f"  Spent: {ToolContext.currency_symbol}{budget['actual_spent']:,.2f} ({budget['percentage_used']:.1f}%)\n"
            result += f"  Remaining: {ToolContext.currency_symbol}{budget['remaining']:,.2f}\n"

            if budget['is_overspent']:
                result += f"  ⚠️ OVER BUDGET!\n"
            elif budget['is_near_limit']:
                result += f"  ⚠️ Near limit!\n"

            result += "\n"

        return result

    except Exception as e:
        return f"❌ Error getting budgets: {str(e)}"


def _create_budget(
    category: str,
    amount: float,
    period: str = "monthly",
    alert_threshold: float = 0.9,
) -> str:
    """
    Create a new budget for a spending category.
    Use this when the user wants to set a spending limit for a category.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        budget = Budget(
            id=str(uuid.uuid4()),
            user_id=user_id,
            category=category.lower(),
            amount=amount,
            period=period,
            start_date=datetime.utcnow(),
            alert_threshold=alert_threshold,
        )

        db.add(budget)
        db.flush()
        db.commit()

        return f"✅ Budget created: {ToolContext.currency_symbol}{amount:,.2f} {period} budget for {category}"

    except Exception as e:
        db.rollback()
        return f"❌ Error creating budget: {str(e)}"


# ============================================================================
# TIER 1 FEATURE TOOLS - Recurring Transactions
# ============================================================================

@tool
def get_recurring_transactions() -> str:
    """
    Get all active recurring transactions (scheduled bills, subscriptions, income).
    Use this when the user asks about recurring payments, subscriptions, or bills.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        recurring = (
            db.query(RecurringTransaction)
            .filter(
                RecurringTransaction.user_id == user_id,
                RecurringTransaction.is_active == True
            )
            .order_by(RecurringTransaction.next_date)
            .all()
        )

        if not recurring:
            return "You don't have any recurring transactions set up yet."

        result = f"📅 Recurring Transactions ({len(recurring)}):\n\n"

        for r in recurring:
            type_emoji = "💰" if r.type == TransactionType.INCOME else "💸"
            result += f"{type_emoji} {r.description}\n"
            result += f"  Amount: {ToolContext.currency_symbol}{r.amount:,.2f}\n"
            result += f"  Frequency: {r.frequency.value}\n"
            result += f"  Next: {r.next_date.strftime('%Y-%m-%d')}\n"
            result += f"  Category: {r.category}\n"
            result += f"  Auto-add: {'Yes' if r.auto_add else 'No'}\n\n"

        return result

    except Exception as e:
        return f"❌ Error getting recurring transactions: {str(e)}"


def _create_recurring_transaction(
    transaction_type: str,
    amount: float,
    description: str,
    category: str,
    frequency: str,
    next_date: str,
    auto_add: bool = True,
) -> str:
    """
    Create a new recurring transaction (subscription, bill, regular income).
    Use this when the user wants to set up automatic tracking of recurring payments or income.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        next_dt = datetime.fromisoformat(next_date)

        recurring = RecurringTransaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=TransactionType(transaction_type.lower()),
            amount=amount,
            description=description,
            category=category,
            frequency=RecurrenceFrequency(frequency.lower()),
            next_date=next_dt,
            auto_add=auto_add,
        )

        db.add(recurring)
        db.flush()  # Flush to catch errors before commit
        db.commit()

        return f"✅ Recurring transaction created: {description} - {ToolContext.currency_symbol}{amount:,.2f} {frequency}"

    except Exception as e:
        db.rollback()  # Rollback on error to clean up session
        return f"❌ Error creating recurring transaction: {str(e)}"


# ============================================================================
# TIER 1 FEATURE TOOLS - Cash Flow Forecasting
# ============================================================================

def _get_cashflow_forecast(
    starting_balance: float,
    forecast_days: int = 90,
) -> str:
    """
    Project future cash flow and predict when you might run out of money.
    Use this when the user asks about future finances, runway, or "when will I run out of money".
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        forecast = CashFlowForecaster.forecast_balance(
            db, user_id, starting_balance, forecast_days
        )

        result = f"💵 Cash Flow Forecast ({forecast_days} days)\n\n"
        result += f"Starting Balance: {ToolContext.currency_symbol}{forecast['starting_balance']:,.2f}\n"
        result += f"Minimum Balance: {ToolContext.currency_symbol}{forecast['min_balance']:,.2f} (on {forecast['min_balance_date']})\n"

        if forecast['runway_days'] <= forecast_days:
            result += f"⚠️ RUNWAY WARNING: You may run out of money in {forecast['runway_days']} days!\n\n"
        else:
            result += f"✅ Runway: More than {forecast_days} days\n\n"

        # Show 30/60/90 day summaries
        for period_name, period_data in forecast['summary_periods'].items():
            days = period_name.split('_')[0]
            result += f"{days}-Day Summary:\n"
            result += f"  Ending Balance: {ToolContext.currency_symbol}{period_data['ending_balance']:,.2f}\n"
            result += f"  Total Income: {ToolContext.currency_symbol}{period_data['total_income']:,.2f}\n"
            result += f"  Total Expenses: {ToolContext.currency_symbol}{period_data['total_expenses']:,.2f}\n"
            result += f"  Net Change: {ToolContext.currency_symbol}{period_data['net_change']:,.2f}\n\n"

        # Show warnings
        if forecast['warnings']:
            result += "⚠️ Warnings:\n"
            for warning in forecast['warnings']:
                result += f"• {warning['message']}\n"

        return result

    except Exception as e:
        return f"❌ Error forecasting cash flow: {str(e)}"


# ============================================================================
# TIER 1 FEATURE TOOLS - Notifications
# ============================================================================

@tool
def get_notifications() -> str:
    """
    Get recent notifications (budget alerts, bill reminders, unusual spending, etc.).
    Use this when the user asks about notifications, alerts, or reminders.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        notifications = (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(10)
            .all()
        )

        if not notifications:
            return "You have no notifications. All clear! ✅"

        unread_count = sum(1 for n in notifications if n.status == NotificationStatus.UNREAD)

        result = f"🔔 Notifications ({unread_count} unread):\n\n"

        for n in notifications:
            status_emoji = "🆕" if n.status == NotificationStatus.UNREAD else "✓"
            priority_emoji = "🔴" if n.priority == 3 else "🟡" if n.priority == 2 else "🟢"

            result += f"{status_emoji} {priority_emoji} {n.title}\n"
            result += f"  {n.message}\n"
            result += f"  {n.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"

        return result

    except Exception as e:
        return f"❌ Error getting notifications: {str(e)}"


@tool
def detect_recurring_patterns() -> str:
    """
    Analyze transaction history to detect recurring patterns (subscriptions, bills, regular income).
    Use this when the user asks about recurring expenses, subscriptions, or to automate transactions.
    This helps identify transactions that should be set up as recurring to improve forecasting.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        patterns = RecurringDetector.detect_patterns(db, user_id)

        if not patterns:
            return "✅ No recurring patterns detected. Keep logging transactions and I'll watch for patterns!"

        result = f"🔍 Detected {len(patterns)} recurring pattern(s):\n\n"

        for i, pattern in enumerate(patterns, 1):
            confidence_emoji = "🟢" if pattern['confidence'] >= 0.8 else "🟡" if pattern['confidence'] >= 0.6 else "🟠"
            
            result += f"{i}. {pattern['description']}\n"
            result += f"   Amount: {ToolContext.currency_symbol}{pattern['amount']:,.2f}\n"
            result += f"   Frequency: {pattern['frequency']}\n"
            result += f"   Type: {pattern['transaction_type']}\n"
            result += f"   Category: {pattern['category']}\n"
            result += f"   Occurrences: {pattern['occurrences']} times\n"
            result += f"   {confidence_emoji} Confidence: {pattern['confidence']*100:.0f}%\n"
            result += f"   Next expected: {pattern['next_date']}\n"
            result += f"   Recent dates: {', '.join(pattern['sample_dates'])}\n\n"

        result += "💡 Tip: Use create_recurring_transaction to automate these and improve cash flow forecasting!"

        return result

    except Exception as e:
        return f"❌ Error detecting patterns: {str(e)}"


# Create StructuredTool instances with Pydantic schemas for strict type validation
add_transaction = StructuredTool.from_function(
    func=_add_transaction,
    name="add_transaction",
    description="""Add a ONE-TIME financial transaction (income, expense, lending, or borrowing).

    Use this ONLY for one-time transactions like:
    - "I spent $50 on groceries today"
    - "Earned $200 from freelance project"
    - "Bought coffee for $5"

    DO NOT use this if the user mentions recurring keywords like:
    - 'per month', 'monthly', 'every month', 'weekly', 'salary', 'subscription', 'bill', 'rent'
    - For those, use create_recurring_transaction instead.""",
    args_schema=AddTransactionInput,
)

get_transactions = StructuredTool.from_function(
    func=_get_transactions,
    name="get_transactions",
    description="Retrieve recent transactions for the user. Use this to show the user their transaction history or analyze spending patterns.",
    args_schema=GetTransactionsInput,
)

add_debt_or_loan = StructuredTool.from_function(
    func=_add_debt_or_loan,
    name="add_debt_or_loan",
    description="""Add a debt (money you owe) or loan (money you lent to someone).

    REQUIRED FIELDS (ALL must be provided):
    - name: Loan/debt name (e.g., "Gold Loan", "Car Loan")
    - amount: Principal amount
    - interest_rate: Annual interest rate as percentage (e.g., 12 for 12%)
    - monthly_payment: Monthly EMI/payment amount
    - debt_type: "debt" or "loan"
    
    IMPORTANT: If user doesn't provide all required fields, ASK for them before calling this tool.
    Do NOT make assumptions about interest rates or EMI amounts.""",
    args_schema=AddDebtLoanInput,
)

optimize_debt_repayment = StructuredTool.from_function(
    func=_optimize_debt_repayment,
    name="optimize_debt_repayment",
    description="""Calculate optimal debt repayment strategy (avalanche vs snowball).

    Use this when:
    - User asks "how to pay off debt faster", "debt strategy", "get out of debt"
    - User provides an extra monthly amount they can pay toward debt
    - User responds with a number after you asked about extra debt payment
    
    IMPORTANT: This tool requires extra_monthly_budget parameter.
    If user just says a number like "1000" or "$500" in context of debt discussion, use that as extra_monthly_budget.""",
    args_schema=OptimizeDebtInput,
)

add_financial_goal = StructuredTool.from_function(
    func=_add_financial_goal,
    name="add_financial_goal",
    description="Create a new financial goal (e.g., emergency fund, vacation, down payment). Use this when the user wants to set a savings goal or target.",
    args_schema=AddGoalInput,
)

project_goal_achievement = StructuredTool.from_function(
    func=_project_goal_achievement,
    name="project_goal_achievement",
    description="Project when a goal will be achieved based on current income and expenses. Use this when the user asks 'when will I reach my goal' or 'can I afford this goal'.",
    args_schema=ProjectGoalInput,
)

# TIER 1 Feature Tools
create_budget = StructuredTool.from_function(
    func=_create_budget,
    name="create_budget",
    description="Create a new budget for a spending category. Use this when the user wants to set a spending limit for a category.",
    args_schema=CreateBudgetInput,
)

create_recurring_transaction = StructuredTool.from_function(
    func=_create_recurring_transaction,
    name="create_recurring_transaction",
    description="""Create a recurring transaction for regular income or expenses that happen repeatedly.

    Use this tool when the user mentions:
    - Time frequency: 'per month', 'per week', 'monthly', 'weekly', 'daily', 'yearly', 'every month', 'bi-weekly', 'quarterly'
    - Recurring income: 'salary', 'paycheck', 'wages', 'monthly income'
    - Recurring expenses: 'subscription', 'bill', 'rent', 'mortgage', 'insurance', 'membership', 'dues'

    Examples:
    - "salary per month 3 lakh" → USE THIS TOOL with frequency='monthly'
    - "Netflix $15 per month" → USE THIS TOOL with frequency='monthly'
    - "rent $2000 every month" → USE THIS TOOL with frequency='monthly'

    Do NOT use add_transaction for these - use this tool instead.""",
    args_schema=CreateRecurringInput,
)

get_cashflow_forecast = StructuredTool.from_function(
    func=_get_cashflow_forecast,
    name="get_cashflow_forecast",
    description="Project future cash flow and predict when you might run out of money. Use this when the user asks about future finances, runway, or 'when will I run out of money'.",
    args_schema=CashFlowForecastInput,
)


# ============================================================================
# Account Management Tools
# ============================================================================


def _add_account(
    account_type: str,
    account_name: str,
    institution_name: str = "",
    current_balance: float = 0.0,
    account_number_last4: str = "",
) -> str:
    """
    Add a new financial account (checking, savings, credit card, etc.).
    Use this when the user wants to track multiple bank accounts.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        # Validate account type
        try:
            account_type_enum = AccountType(account_type.lower())
        except ValueError:
            return f"❌ Invalid account type. Must be one of: {', '.join([t.value for t in AccountType])}"

        # Create account
        account = Account(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_type=account_type_enum,
            account_name=account_name,
            institution_name=institution_name if institution_name else None,
            current_balance=current_balance,
            account_number_last4=account_number_last4 if account_number_last4 else None,
            status=AccountStatus.ACTIVE,
        )

        db.add(account)
        db.flush()
        db.commit()
        db.refresh(account)

        return f"✅ Account added successfully: {account_name} ({account_type}) with balance ${current_balance:.2f}. Account ID: {account.id}"

    except Exception as e:
        db.rollback()
        return f"❌ Error adding account: {str(e)}"


def _get_accounts() -> str:
    """
    Get all accounts for the user.
    Use this to show the user their accounts or get account balances.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        accounts = db.query(Account).filter(Account.user_id == user_id).all()

        if not accounts:
            return "No accounts found. You can add accounts to track your finances across multiple bank accounts."

        result = f"Found {len(accounts)} account(s):\n\n"
        total_balance = 0.0

        for acc in accounts:
            result += f"• {acc.account_name} ({acc.account_type.value})\n"
            result += f"  Balance: ${acc.current_balance:.2f}"
            if acc.institution_name:
                result += f" | {acc.institution_name}"
            if acc.account_number_last4:
                result += f" | ****{acc.account_number_last4}"
            result += f"\n  Status: {acc.status.value}\n"

            # Include credit card details if available
            if acc.account_type == AccountType.CREDIT_CARD and acc.credit_card_details:
                cc = acc.credit_card_details
                result += f"  Credit Limit: ${cc.credit_limit:.2f}\n"
                result += f"  Available: ${cc.available_credit:.2f}\n"
                result += f"  Utilization: {cc.credit_utilization:.1f}%\n"
                if cc.payment_due_date:
                    result += f"  Due Date: {cc.payment_due_date.strftime('%Y-%m-%d')}\n"
                if cc.minimum_payment:
                    result += f"  Minimum Payment: ${cc.minimum_payment:.2f}\n"

            result += "\n"

            # Sum balances (excluding credit cards which are liabilities)
            if acc.account_type != AccountType.CREDIT_CARD:
                total_balance += acc.current_balance

        result += f"Total Balance (excluding credit cards): ${total_balance:.2f}"

        return result

    except Exception as e:
        return f"❌ Error retrieving accounts: {str(e)}"


def _add_credit_card(
    account_id: str,
    credit_limit: float,
    available_credit: float,
    apr: float = 0.0,
    minimum_payment: float = 0.0,
    payment_due_date: str = "",
    card_network: str = "",
) -> str:
    """
    Add credit card details to an existing credit card account.
    Use this when the user wants to track credit card specific information like credit limit, APR, etc.
    """
    try:
        db = ToolContext.db
        user_id = ToolContext.user_id

        # Verify account exists and is owned by user
        account = db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == user_id
        ).first()

        if not account:
            return "❌ Account not found. Please create a credit card account first using add_account."

        if account.account_type != AccountType.CREDIT_CARD:
            return "❌ This account is not a credit card account. Please use a credit_card type account."

        # Check if credit card details already exist
        existing_cc = db.query(CreditCard).filter(CreditCard.account_id == account_id).first()
        if existing_cc:
            return "❌ Credit card details already exist for this account."

        # Parse payment due date if provided
        due_date = None
        if payment_due_date:
            try:
                due_date = datetime.fromisoformat(payment_due_date)
            except ValueError:
                return "❌ Invalid payment_due_date format. Use YYYY-MM-DD format."

        # Validate card network if provided
        card_network_enum = None
        if card_network:
            try:
                card_network_enum = CardNetwork(card_network.lower())
            except ValueError:
                return f"❌ Invalid card network. Must be one of: {', '.join([n.value for n in CardNetwork])}"

        # Calculate credit utilization
        credit_utilization = 0.0
        if credit_limit > 0:
            balance = abs(account.current_balance) if account.current_balance < 0 else 0
            credit_utilization = (balance / credit_limit) * 100

        # Create credit card details
        credit_card = CreditCard(
            id=str(uuid.uuid4()),
            account_id=account_id,
            credit_limit=credit_limit,
            available_credit=available_credit,
            apr=apr if apr > 0 else None,
            minimum_payment=minimum_payment,
            payment_due_date=due_date,
            card_network=card_network_enum,
            credit_utilization=credit_utilization,
        )

        db.add(credit_card)
        db.flush()
        db.commit()
        db.refresh(credit_card)

        result = f"✅ Credit card details added successfully!\n"
        result += f"Credit Limit: ${credit_limit:.2f}\n"
        result += f"Available Credit: ${available_credit:.2f}\n"
        result += f"Utilization: {credit_utilization:.1f}%"
        if apr > 0:
            result += f"\nAPR: {apr:.2f}%"
        if due_date:
            result += f"\nPayment Due: {due_date.strftime('%Y-%m-%d')}"

        return result

    except Exception as e:
        db.rollback()
        return f"❌ Error adding credit card details: {str(e)}"


add_account = StructuredTool.from_function(
    func=_add_account,
    name="add_account",
    description="""Add a new financial account to track.

    Use this when the user mentions:
    - Bank accounts: 'checking account', 'savings account', 'bank account'
    - Credit cards: 'credit card', 'visa', 'mastercard'
    - Other accounts: 'investment account', 'cash', 'wallet'

    Examples:
    - "I have a Chase checking account with $5000"
    - "Add my savings account at Wells Fargo"
    - "Track my Amex credit card"
    """,
    args_schema=AddAccountInput,
)

get_accounts = StructuredTool.from_function(
    func=_get_accounts,
    name="get_accounts",
    description="""Get all financial accounts for the user.

    Use this when the user asks:
    - "Show my accounts"
    - "What accounts do I have?"
    - "List my bank accounts"
    - "What's my account balance?"
    """,
)

add_credit_card = StructuredTool.from_function(
    func=_add_credit_card,
    name="add_credit_card",
    description="""Add credit card specific details to a credit card account.

    Use this after creating a credit card account to add details like:
    - Credit limit
    - APR (interest rate)
    - Payment due date
    - Available credit

    The user must have created a credit_card type account first.
    """,
    args_schema=AddCreditCardInput,
)


# ============================================================================
# ADVANCED FEATURES (2025) - Dynamic Budgeting, Milestones, Simulation
# ============================================================================


@tool
def analyze_budget_adjustments() -> str:
    """
    Analyze budgets and get AI-powered adjustment recommendations.
    
    Use this when the user asks:
    - "Should I adjust my budgets?"
    - "How can I optimize my spending?"
    - "I'm overspending, what should I do?"
    
    Returns dynamic budget recommendations based on spending patterns.
    """
    from ..services.dynamic_budget_adjuster import DynamicBudgetAdjuster
    
    try:
        user_id = get_user_context()["user_id"]
        db = get_user_context()["db"]
        
        analysis = DynamicBudgetAdjuster.analyze_and_adjust_budgets(db, user_id)
        
        if analysis["status"] == "no_budgets":
            return "No active budgets found. Create budgets first using create_budget."
        
        result = f"📊 Budget Analysis:\n\n"
        result += f"Total Budgets: {analysis['total_budgets']}\n"
        result += f"Overspent Categories: {analysis['overspent_categories']}\n\n"
        
        if analysis["adjustments"]:
            result += "💡 Recommended Adjustments:\n\n"
            for adj in analysis["adjustments"][:5]:  # Show top 5
                change_emoji = "📉" if adj["change"] < 0 else "📈"
                result += f"{change_emoji} {adj['category'].title()}: "
                result += f"${adj['current_amount']:,.2f} → ${adj['new_amount']:,.2f} "
                result += f"({adj['change']:+,.2f})\n"
                result += f"   Reason: {adj['reason']}\n\n"
        else:
            result += "✅ Your budgets look well-balanced!\n"
        
        return result
        
    except Exception as e:
        return f"Error analyzing budgets: {str(e)}"


@tool
def get_goal_milestones() -> str:
    """
    Get AI-adjusted milestones for all active goals.
    
    Use this when the user asks:
    - "How am I tracking on my goals?"
    - "When will I reach my savings goal?"
    - "Show my goal progress"
    
    Returns adaptive milestones that adjust based on current savings rate.
    """
    from ..services.goal_milestone_adjuster import GoalMilestoneAdjuster
    
    try:
        user_id = get_user_context()["user_id"]
        db = get_user_context()["db"]
        
        milestones = GoalMilestoneAdjuster.get_all_goal_milestones(db, user_id)
        
        if not milestones:
            return "No active goals found. Create a goal first using add_financial_goal."
        
        result = "🎯 Goal Milestones & Progress:\n\n"
        
        for goal_data in milestones:
            status_emoji = "✅" if goal_data["on_track"] else "⚠️"
            result += f"{status_emoji} {goal_data['goal_name']}\n"
            result += f"   Progress: ${goal_data['current_amount']:,.2f} / ${goal_data['target_amount']:,.2f} "
            result += f"({goal_data['progress_percentage']:.1f}%)\n"
            result += f"   Required: ${goal_data['required_monthly_contribution']:,.2f}/month\n"
            result += f"   Current Savings: ${goal_data['current_monthly_savings']:,.2f}/month\n"
            result += f"   Status: {'On Track' if goal_data['on_track'] else 'Behind Schedule'}\n\n"
            
            # Show next milestone
            next_milestone = next(
                (m for m in goal_data["milestones"] if not m["is_achieved"]),
                None
            )
            if next_milestone:
                result += f"   Next Milestone: {next_milestone['percentage']}% "
                result += f"(${next_milestone['amount']:,.2f}) by {next_milestone['estimated_date']}\n"
            
            # Show top recommendation
            if goal_data["recommendations"]:
                result += f"   💡 {goal_data['recommendations'][0]}\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"Error getting goal milestones: {str(e)}"


class SimulationInput(BaseModel):
    """Input schema for run_simulation tool"""
    scenario_type: str = Field(description="Scenario type: income_change, expense_change, budget_cut, new_recurring, goal_acceleration")
    change_amount: float = Field(description="Amount of change (monthly basis)")
    forecast_days: int = Field(default=180, description="Days to forecast (default 180)")


@tool
def run_simulation(
    scenario_type: str,
    change_amount: float,
    forecast_days: int = 180,
) -> str:
    """
    Run a financial "what-if" simulation to see impact of changes.
    
    Use this when the user asks:
    - "What if I save $500 more per month?"
    - "What if I cut my spending by $300?"
    - "What if I get a raise?"
    - "Can I afford a new subscription?"
    
    Scenario types:
    - income_change: Simulate income increase/decrease
    - expense_change: Simulate expense increase/decrease
    - new_recurring: Simulate adding a new recurring expense
    
    Args:
        scenario_type: Type of scenario to simulate
        change_amount: Monthly change amount (positive for increase, negative for decrease)
        forecast_days: Days to forecast (default 180)
    
    Returns:
        Comparison of baseline vs scenario with recommendation
    """
    from ..services.financial_simulator import FinancialSimulator
    
    try:
        user_id = get_user_context()["user_id"]
        db = get_user_context()["db"]
        
        # Build parameters based on scenario type
        parameters = {
            "change_amount": change_amount,
            "starting_balance": 10000,  # Default, should be calculated from actual balance
        }
        
        if scenario_type == "new_recurring":
            parameters["amount"] = abs(change_amount)
            parameters["frequency"] = "monthly"
            parameters["type"] = "expense" if change_amount > 0 else "income"
        
        result_data = FinancialSimulator.simulate_scenario(
            db, user_id, scenario_type, parameters, forecast_days
        )
        
        baseline = result_data["baseline"]
        scenario = result_data["scenario"]
        comparison = result_data["comparison"]
        
        result = f"🔮 Financial Simulation ({forecast_days} days):\n\n"
        
        result += "📊 Current Path (Baseline):\n"
        result += f"   Ending Balance: ${baseline['ending_balance']:,.2f}\n"
        result += f"   Total Income: ${baseline['total_income']:,.2f}\n"
        result += f"   Total Expenses: ${baseline['total_expenses']:,.2f}\n"
        result += f"   Runway: {baseline['runway_days']} days\n\n"
        
        result += f"🎯 With Change ({scenario_type}):\n"
        result += f"   Ending Balance: ${scenario['ending_balance']:,.2f}\n"
        result += f"   Total Income: ${scenario['total_income']:,.2f}\n"
        result += f"   Total Expenses: ${scenario['total_expenses']:,.2f}\n"
        result += f"   Runway: {scenario['runway_days']} days\n\n"
        
        result += "📈 Impact:\n"
        result += f"   Balance Difference: ${comparison['balance_difference']:+,.2f} "
        result += f"({comparison['balance_change_percentage']:+.1f}%)\n"
        result += f"   Runway Change: {comparison['runway_difference_days']:+d} days\n\n"
        
        result += f"💡 {result_data['recommendation']}\n"
        
        return result
        
    except Exception as e:
        return f"Error running simulation: {str(e)}"


@tool
def suggest_category(description: str) -> str:
    """
    Suggest a category for a transaction based on description.
    
    Use this when categorizing transactions or when user asks
    "what category should this be?"
    
    Args:
        description: Transaction description
    
    Returns:
        Suggested category with full hierarchical path
    """
    from ..database.category_hierarchy import CATEGORY_HIERARCHY
    
    try:
        category = CATEGORY_HIERARCHY.suggest_category(description)
        path = CATEGORY_HIERARCHY.get_full_path(category)
        
        return f"Suggested category: {category}\nFull path: {path}"
        
    except Exception as e:
        return f"Error suggesting category: {str(e)}"


# List of all tools for the agent (TIER 1 + Original + Advanced)
financial_tools = [
    # Original tools
    add_transaction,
    get_transactions,
    calculate_financial_health,
    add_debt_or_loan,
    get_debts_and_loans,
    optimize_debt_repayment,
    add_financial_goal,
    get_goals,
    project_goal_achievement,
    analyze_spending_by_category,

    # TIER 1 Critical Features
    get_budgets,
    create_budget,
    get_recurring_transactions,
    create_recurring_transaction,
    get_cashflow_forecast,
    get_notifications,
    detect_recurring_patterns,  # Smart pattern detection

    # Account Management
    add_account,
    get_accounts,
    add_credit_card,
    
    # Advanced Features (2025)
    analyze_budget_adjustments,
    get_goal_milestones,
    run_simulation,
    suggest_category,
]
