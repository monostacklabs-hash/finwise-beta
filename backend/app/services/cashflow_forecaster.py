"""
Cash Flow Forecasting Service - TIER 1 Feature
Projects future balances based on historical data and recurring transactions
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from statistics import mean, median

from ..database.models import (
    Transaction,
    TransactionType,
    RecurringTransaction,
    RecurrenceFrequency,
    Notification,
    NotificationType,
    NotificationStatus,
)
import uuid

logger = logging.getLogger(__name__)


class CashFlowForecaster:
    """Service for forecasting cash flow and predicting financial runway"""

    @staticmethod
    def forecast_balance(
        db: Session,
        user_id: str,
        starting_balance: float,
        forecast_days: int = 90,
        current_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Forecast cash balance for the next N days

        Args:
            db: Database session
            user_id: User ID
            starting_balance: Current account balance
            forecast_days: Number of days to forecast (default 90)
            current_date: Current date (defaults to now)

        Returns:
            Dict with forecast data including daily balances, low points, runway
        """
        if current_date is None:
            current_date = datetime.utcnow()

        # Get historical data for pattern analysis
        lookback_days = 90
        historical_start = current_date - timedelta(days=lookback_days)

        historical_income = CashFlowForecaster._get_historical_averages(
            db, user_id, historical_start, current_date, TransactionType.INCOME
        )

        historical_expenses = CashFlowForecaster._get_historical_averages(
            db, user_id, historical_start, current_date, TransactionType.EXPENSE
        )

        # Get all scheduled recurring transactions
        recurring_transactions = db.query(RecurringTransaction).filter(
            and_(
                RecurringTransaction.user_id == user_id,
                RecurringTransaction.is_active == True
            )
        ).all()

        # Project daily balances
        daily_balances = []
        current_balance = starting_balance

        forecast_end = current_date + timedelta(days=forecast_days)

        # Create day-by-day projection
        for day_offset in range(forecast_days + 1):
            projection_date = current_date + timedelta(days=day_offset)

            # Add scheduled transactions for this day
            day_income = 0
            day_expenses = 0

            for recurring in recurring_transactions:
                if CashFlowForecaster._is_due_on_date(recurring, projection_date):
                    if recurring.type == TransactionType.INCOME:
                        day_income += recurring.amount
                    elif recurring.type == TransactionType.EXPENSE:
                        day_expenses += recurring.amount

            # Add average daily historical spending if no specific transactions
            if day_expenses == 0:
                day_expenses = historical_expenses["daily_average"]

            # Add average daily historical income if no specific transactions
            if day_income == 0:
                day_income = historical_income["daily_average"]

            # Calculate balance
            current_balance = current_balance + day_income - day_expenses

            daily_balances.append({
                "date": projection_date.strftime("%Y-%m-%d"),
                "balance": round(current_balance, 2),
                "income": round(day_income, 2),
                "expenses": round(day_expenses, 2),
                "net": round(day_income - day_expenses, 2),
            })

        # Calculate key metrics
        min_balance_day = min(daily_balances, key=lambda x: x["balance"])

        # Calculate runway (days until balance hits $0)
        runway_days = None
        for i, day in enumerate(daily_balances):
            if day["balance"] <= 0:
                runway_days = i
                break

        # If never hits 0, runway is unlimited
        if runway_days is None:
            runway_days = forecast_days + 1  # Beyond forecast window

        # Generate warnings
        warnings = []
        if runway_days <= 30:
            warnings.append({
                "type": "critical",
                "message": f"Warning: You may run out of money in {runway_days} days",
                "days_until": runway_days,
            })
            # Create notification
            CashFlowForecaster._create_low_balance_notification(
                db, user_id, runway_days, min_balance_day["balance"]
            )
        elif min_balance_day["balance"] < (starting_balance * 0.2):
            warnings.append({
                "type": "warning",
                "message": f"Your balance will drop to ${min_balance_day['balance']:,.2f} on {min_balance_day['date']}",
                "min_balance": min_balance_day["balance"],
                "date": min_balance_day["date"],
            })

        # Calculate 30/60/90 day summary
        summary_periods = []
        for period_days in [30, 60, 90]:
            if period_days <= forecast_days:
                period_start_date = current_date
                period_end_date = current_date + timedelta(days=period_days)
                period_end_balance = daily_balances[period_days]["balance"]
                period_total_income = sum(d["income"] for d in daily_balances[:period_days + 1])
                period_total_expenses = sum(d["expenses"] for d in daily_balances[:period_days + 1])

                summary_periods.append({
                    "period": f"{period_days} Days",
                    "period_start": period_start_date.strftime("%Y-%m-%d"),
                    "period_end": period_end_date.strftime("%Y-%m-%d"),
                    "starting_balance": starting_balance,
                    "ending_balance": round(period_end_balance, 2),
                    "total_income": round(period_total_income, 2),
                    "total_expenses": round(period_total_expenses, 2),
                    "net_change": round(period_end_balance - starting_balance, 2),
                })

        return {
            "starting_balance": starting_balance,
            "forecast_days": forecast_days,
            "forecast_start_date": current_date.strftime("%Y-%m-%d"),
            "forecast_end_date": forecast_end.strftime("%Y-%m-%d"),
            "daily_balances": daily_balances,
            "min_balance": min_balance_day["balance"],
            "min_balance_date": min_balance_day["date"],
            "runway_days": runway_days,
            "warnings": warnings,
            "summary_periods": summary_periods,
            "historical_averages": {
                "daily_income": historical_income["daily_average"],
                "daily_expenses": historical_expenses["daily_average"],
                "monthly_income": historical_income["monthly_average"],
                "monthly_expenses": historical_expenses["monthly_average"],
            },
        }

    @staticmethod
    def _get_historical_averages(
        db: Session,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        transaction_type: TransactionType,
    ) -> Dict:
        """
        Calculate historical averages for income or expenses

        Args:
            db: Database session
            user_id: User ID
            start_date: Start date
            end_date: End date
            transaction_type: Type of transaction

        Returns:
            Dict with daily and monthly averages
        """
        # Use SQL aggregations for better performance
        result = db.query(
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.type == transaction_type,
                Transaction.date >= start_date,
                Transaction.date < end_date
            )
        ).first()

        total = result.total or 0.0
        count = result.count or 0

        if total == 0:
            return {
                "daily_average": 0,
                "monthly_average": 0,
                "total": 0,
                "count": 0,
            }

        days = (end_date - start_date).days or 1
        daily_avg = total / days
        monthly_avg = daily_avg * 30

        return {
            "daily_average": round(daily_avg, 2),
            "monthly_average": round(monthly_avg, 2),
            "total": round(total, 2),
            "count": count,
        }

    @staticmethod
    def _is_due_on_date(recurring: RecurringTransaction, check_date: datetime) -> bool:
        """
        Check if a recurring transaction is due on a specific date

        Args:
            recurring: RecurringTransaction object
            check_date: Date to check

        Returns:
            True if due on this date
        """
        # Check if the recurring transaction's next_date matches check_date
        if recurring.next_date.date() == check_date.date():
            return True

        # For more complex frequency checking, we need to calculate all occurrences
        # This is a simplified version - a full implementation would need to
        # calculate all future occurrences up to check_date

        return False

    @staticmethod
    def _create_low_balance_notification(
        db: Session,
        user_id: str,
        runway_days: int,
        projected_min_balance: float,
    ):
        """
        Create a low balance warning notification

        Args:
            db: Database session
            user_id: User ID
            runway_days: Days until balance reaches $0
            projected_min_balance: Minimum projected balance
        """
        # Check if we already created this notification today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        existing = db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.type == NotificationType.LOW_BALANCE,
                Notification.created_at >= today_start
            )
        ).first()

        if existing:
            return

        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=NotificationType.LOW_BALANCE,
            title="Low Balance Warning",
            message=f"Based on your spending patterns, you may run out of money in {runway_days} days. Your balance is projected to drop to ${projected_min_balance:,.2f}. Consider reducing expenses or increasing income.",
            status=NotificationStatus.UNREAD,
            priority=3,  # High priority
            action_url="/forecast",
            extra_data=f'{{"runway_days": {runway_days}, "min_balance": {projected_min_balance}}}',
        )

        db.add(notification)
        db.commit()
        logger.info(f"Created low balance notification for user {user_id}")
