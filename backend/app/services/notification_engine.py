"""
Smart Notification Engine - TIER 1 Feature
Detects unusual spending, goal milestones, and other financial events
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import Dict, List
from statistics import mean, stdev
import logging
import uuid

from ..database.models import (
    Transaction,
    TransactionType,
    Goal,
    GoalStatus,
    DebtLoan,
    DebtLoanStatus,
    Notification,
    NotificationType,
    NotificationStatus,
)

logger = logging.getLogger(__name__)


class NotificationEngine:
    """Service for detecting financial events and creating smart notifications"""

    @staticmethod
    def detect_unusual_spending(
        db: Session,
        user_id: str,
        new_transaction: Transaction,
    ) -> bool:
        """
        Detect if a transaction represents unusual spending

        Args:
            db: Database session
            user_id: User ID
            new_transaction: The newly created transaction

        Returns:
            True if notification was created
        """
        # Only check expenses
        if new_transaction.type != TransactionType.EXPENSE:
            return False

        # Get historical transactions in same category
        lookback_days = 90
        lookback_start = datetime.utcnow() - timedelta(days=lookback_days)

        historical = db.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.category == new_transaction.category,
                Transaction.date >= lookback_start,
                Transaction.id != new_transaction.id  # Exclude the new one
            )
        ).all()

        if len(historical) < 3:
            # Not enough data
            return False

        amounts = [txn.amount for txn in historical]
        avg_amount = mean(amounts)

        # Calculate standard deviation if we have enough data
        if len(amounts) >= 5:
            std_amount = stdev(amounts)
            # Flag if transaction is more than 2 standard deviations above mean
            threshold = avg_amount + (2 * std_amount)
        else:
            # Use 2x average as threshold if not enough data for stdev
            threshold = avg_amount * 2

        if new_transaction.amount > threshold:
            # This is unusual spending
            NotificationEngine._create_unusual_spending_notification(
                db, user_id, new_transaction, avg_amount
            )
            return True

        return False

    @staticmethod
    def check_goal_milestones(
        db: Session,
        user_id: str,
        goal_id: str,
    ) -> bool:
        """
        Check if a goal has reached a milestone (25%, 50%, 75%, 100%)

        Args:
            db: Database session
            user_id: User ID
            goal_id: Goal ID

        Returns:
            True if notification was created
        """
        goal = db.query(Goal).filter(
            and_(
                Goal.id == goal_id,
                Goal.user_id == user_id
            )
        ).first()

        if not goal or goal.target_amount == 0:
            return False

        percentage = (goal.current_amount / goal.target_amount) * 100

        # Check for milestone achievements
        milestones = [25, 50, 75]
        for milestone in milestones:
            if percentage >= milestone and percentage < milestone + 5:  # 5% buffer
                # Check if we already sent this milestone notification
                existing = db.query(Notification).filter(
                    and_(
                        Notification.user_id == user_id,
                        Notification.type == NotificationType.GOAL_MILESTONE,
                        Notification.extra_data.contains(f'"goal_id": "{goal_id}"'),
                        Notification.extra_data.contains(f'"milestone": {milestone}')
                    )
                ).first()

                if not existing:
                    NotificationEngine._create_goal_milestone_notification(
                        db, user_id, goal, milestone
                    )
                    return True

        # Check for goal completion
        if percentage >= 100:
            NotificationEngine._create_goal_completed_notification(
                db, user_id, goal
            )
            # Update goal status
            goal.status = GoalStatus.COMPLETED
            db.commit()
            return True

        return False

    @staticmethod
    def check_debt_paid_off(
        db: Session,
        user_id: str,
        debt_id: str,
    ) -> bool:
        """
        Check if a debt has been paid off

        Args:
            db: Database session
            user_id: User ID
            debt_id: Debt ID

        Returns:
            True if notification was created
        """
        debt = db.query(DebtLoan).filter(
            and_(
                DebtLoan.id == debt_id,
                DebtLoan.user_id == user_id
            )
        ).first()

        if not debt:
            return False

        if debt.remaining_amount <= 0 and debt.status == DebtLoanStatus.ACTIVE:
            # Debt is paid off!
            NotificationEngine._create_debt_paid_off_notification(
                db, user_id, debt
            )
            # Update debt status
            debt.status = DebtLoanStatus.PAID_OFF
            db.commit()
            return True

        return False

    @staticmethod
    def _create_unusual_spending_notification(
        db: Session,
        user_id: str,
        transaction: Transaction,
        avg_amount: float,
    ):
        """Create notification for unusual spending"""
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=NotificationType.UNUSUAL_SPENDING,
            title="Unusual Spending Detected",
            message=f"You spent ${transaction.amount:,.2f} on {transaction.description} ({transaction.category}). This is significantly higher than your average of ${avg_amount:,.2f} for this category.",
            status=NotificationStatus.UNREAD,
            priority=2,
            action_url=f"/transactions/{transaction.id}",
            extra_data=f'{{"transaction_id": "{transaction.id}", "amount": {transaction.amount}, "average": {avg_amount}}}',
        )
        db.add(notification)
        db.commit()
        logger.info(f"Created unusual spending notification for user {user_id}")

    @staticmethod
    def _create_goal_milestone_notification(
        db: Session,
        user_id: str,
        goal: Goal,
        milestone: int,
    ):
        """Create notification for goal milestone"""
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=NotificationType.GOAL_MILESTONE,
            title=f"Goal Milestone: {milestone}% Complete!",
            message=f"Congratulations! You've reached {milestone}% of your goal '{goal.name}'. You've saved ${goal.current_amount:,.2f} out of ${goal.target_amount:,.2f}. Keep up the great work!",
            status=NotificationStatus.UNREAD,
            priority=1,
            action_url=f"/goals/{goal.id}",
            extra_data=f'{{"goal_id": "{goal.id}", "milestone": {milestone}, "current": {goal.current_amount}, "target": {goal.target_amount}}}',
        )
        db.add(notification)
        db.commit()
        logger.info(f"Created goal milestone notification for user {user_id}, goal {goal.id}")

    @staticmethod
    def _create_goal_completed_notification(
        db: Session,
        user_id: str,
        goal: Goal,
    ):
        """Create notification for goal completion"""
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=NotificationType.GOAL_COMPLETED,
            title=f"Goal Completed: {goal.name}!",
            message=f"🎉 Congratulations! You've achieved your goal '{goal.name}'! You've saved ${goal.current_amount:,.2f}. Time to celebrate and set a new goal!",
            status=NotificationStatus.UNREAD,
            priority=1,
            action_url=f"/goals/{goal.id}",
            extra_data=f'{{"goal_id": "{goal.id}", "amount": {goal.current_amount}}}',
        )
        db.add(notification)
        db.commit()
        logger.info(f"Created goal completed notification for user {user_id}, goal {goal.id}")

    @staticmethod
    def _create_debt_paid_off_notification(
        db: Session,
        user_id: str,
        debt: DebtLoan,
    ):
        """Create notification for debt paid off"""
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=NotificationType.DEBT_PAID_OFF,
            title=f"Debt Paid Off: {debt.name}!",
            message=f"🎉 Congratulations! You've completely paid off your debt '{debt.name}'! You paid a total of ${debt.principal_amount:,.2f}. This is a huge financial milestone!",
            status=NotificationStatus.UNREAD,
            priority=1,
            action_url=f"/debts/{debt.id}",
            extra_data=f'{{"debt_id": "{debt.id}", "amount": {debt.principal_amount}}}',
        )
        db.add(notification)
        db.commit()
        logger.info(f"Created debt paid off notification for user {user_id}, debt {debt.id}")
