"""
Budget Tracking Service - TIER 1 Feature
Handles budget vs actual tracking and overspending detection
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, extract, func, case
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from ..database.models import Budget, Transaction, TransactionType, Notification, NotificationType, NotificationStatus
import uuid

logger = logging.getLogger(__name__)


class BudgetTracker:
    """Service for tracking budgets and detecting overspending"""

    @staticmethod
    def calculate_budget_status(
        db: Session,
        user_id: str,
        budget_id: str,
        current_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Calculate budget vs actual spending for a specific budget

        Args:
            db: Database session
            user_id: User ID
            budget_id: Budget ID
            current_date: Current date (defaults to now)

        Returns:
            Dict with budget status including spent amount, remaining, percentage
        """
        if current_date is None:
            current_date = datetime.utcnow()

        # Get budget
        budget = db.query(Budget).filter(
            and_(
                Budget.id == budget_id,
                Budget.user_id == user_id,
                Budget.is_active == True
            )
        ).first()

        if not budget:
            raise ValueError("Budget not found")

        # Determine period start and end dates
        period_start, period_end = BudgetTracker._get_period_dates(
            budget, current_date
        )

        # Calculate actual spending in this period
        actual_spent = BudgetTracker._calculate_actual_spending(
            db, user_id, budget.category, period_start, period_end
        )

        # Calculate metrics
        remaining = budget.amount - actual_spent
        percentage = (actual_spent / budget.amount * 100) if budget.amount > 0 else 0
        is_overspent = actual_spent > budget.amount
        is_near_limit = percentage >= (budget.alert_threshold * 100)

        # Check if notification needed
        if is_near_limit and not is_overspent:
            BudgetTracker._create_budget_alert(
                db, user_id, budget, actual_spent, percentage, "warning"
            )
        elif is_overspent:
            BudgetTracker._create_budget_alert(
                db, user_id, budget, actual_spent, percentage, "overspent"
            )

        return {
            "budget_id": budget.id,
            "category": budget.category,
            "period": budget.period,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "budgeted_amount": budget.amount,
            "actual_spent": actual_spent,
            "remaining": remaining,
            "percentage_used": round(percentage, 2),
            "is_overspent": is_overspent,
            "is_near_limit": is_near_limit,
            "alert_threshold": budget.alert_threshold,
        }

    @staticmethod
    def get_all_budget_statuses(
        db: Session,
        user_id: str,
        current_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Get budget status for all active budgets

        Args:
            db: Database session
            user_id: User ID
            current_date: Current date (defaults to now)

        Returns:
            List of budget statuses
        """
        if current_date is None:
            current_date = datetime.utcnow()

        # Get all active budgets
        budgets = db.query(Budget).filter(
            and_(
                Budget.user_id == user_id,
                Budget.is_active == True
            )
        ).all()

        statuses = []
        for budget in budgets:
            try:
                status = BudgetTracker.calculate_budget_status(
                    db, user_id, budget.id, current_date
                )
                statuses.append(status)
            except Exception as e:
                logger.error(f"Error calculating budget status for {budget.id}: {e}")
                continue

        return statuses

    @staticmethod
    def get_spending_by_category(
        db: Session,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, float]:
        """
        Get total spending by category for a date range

        Args:
            db: Database session
            user_id: User ID
            start_date: Start date
            end_date: End date

        Returns:
            Dict mapping category to total spent
        """
        # Use SQL GROUP BY for efficient aggregation
        from sqlalchemy import case
        
        results = db.query(
            case(
                (Transaction.category == None, "uncategorized"),
                (Transaction.category == "", "uncategorized"),
                else_=Transaction.category
            ).label('category'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        ).group_by('category').all()

        spending_by_category = {row.category: row.total for row in results}
        return spending_by_category

    @staticmethod
    def _get_period_dates(budget: Budget, current_date: datetime) -> tuple:
        """
        Calculate period start and end dates based on budget period

        Args:
            budget: Budget object
            current_date: Current date

        Returns:
            Tuple of (start_date, end_date)
        """
        if budget.period == "weekly":
            # Start of week (Monday)
            start = current_date - timedelta(days=current_date.weekday())
            end = start + timedelta(days=7)
        elif budget.period == "monthly":
            # Start of month
            start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # End of month
            if current_date.month == 12:
                end = start.replace(year=current_date.year + 1, month=1)
            else:
                end = start.replace(month=current_date.month + 1)
        elif budget.period == "yearly":
            # Start of year
            start = current_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=current_date.year + 1)
        else:
            # Default to monthly
            start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if current_date.month == 12:
                end = start.replace(year=current_date.year + 1, month=1)
            else:
                end = start.replace(month=current_date.month + 1)

        return start, end

    @staticmethod
    def _calculate_actual_spending(
        db: Session,
        user_id: str,
        category: str,
        start_date: datetime,
        end_date: datetime,
    ) -> float:
        """
        Calculate actual spending for a category in a date range

        Args:
            db: Database session
            user_id: User ID
            category: Category name
            start_date: Period start
            end_date: Period end

        Returns:
            Total spent amount
        """
        # Use SQL aggregation for better performance
        total = db.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.category == category,
                Transaction.date >= start_date,
                Transaction.date < end_date
            )
        ).scalar() or 0.0

        return total

    @staticmethod
    def _create_budget_alert(
        db: Session,
        user_id: str,
        budget: Budget,
        actual_spent: float,
        percentage: float,
        alert_type: str,
    ):
        """
        Create a budget alert notification

        Args:
            db: Database session
            user_id: User ID
            budget: Budget object
            actual_spent: Actual amount spent
            percentage: Percentage of budget used
            alert_type: "warning" or "overspent"
        """
        # Check if we already created an alert for this budget today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        existing_alert = db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.type == NotificationType.BUDGET_ALERT,
                Notification.created_at >= today_start,
                Notification.extra_data.contains(budget.id)
            )
        ).first()

        if existing_alert:
            return  # Don't create duplicate alerts

        if alert_type == "warning":
            title = f"Budget Alert: {budget.category.title()}"
            message = f"You've used {percentage:.1f}% of your ${budget.amount:,.2f} {budget.period} budget for {budget.category}. You've spent ${actual_spent:,.2f}."
            priority = 2  # Medium
        else:  # overspent
            title = f"Budget Exceeded: {budget.category.title()}"
            message = f"You've exceeded your ${budget.amount:,.2f} {budget.period} budget for {budget.category}. You've spent ${actual_spent:,.2f} ({percentage:.1f}%)."
            priority = 3  # High

        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=NotificationType.BUDGET_ALERT,
            title=title,
            message=message,
            status=NotificationStatus.UNREAD,
            priority=priority,
            action_url=f"/budgets/{budget.id}",
            extra_data=f'{{"budget_id": "{budget.id}", "category": "{budget.category}", "alert_type": "{alert_type}"}}',
        )

        db.add(notification)
        db.commit()
        logger.info(f"Created budget alert for user {user_id}, budget {budget.id}")
