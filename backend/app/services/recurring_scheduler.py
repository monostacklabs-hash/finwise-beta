"""
Recurring Transaction Scheduler - TIER 1 Feature
Handles automatic creation of recurring transactions and bill reminders
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import List, Dict
import logging
import uuid

from ..database.models import (
    RecurringTransaction,
    Transaction,
    Notification,
    NotificationType,
    NotificationStatus,
    RecurrenceFrequency,
)

logger = logging.getLogger(__name__)


class RecurringScheduler:
    """Service for processing recurring transactions and reminders"""

    @staticmethod
    def process_due_transactions(db: Session) -> Dict[str, int]:
        """
        Process all due recurring transactions across all users

        This should be called by a scheduled job (e.g., daily cron)

        Args:
            db: Database session

        Returns:
            Dict with processing statistics
        """
        current_date = datetime.utcnow()
        stats = {
            "processed": 0,
            "created_transactions": 0,
            "created_reminders": 0,
            "errors": 0,
        }

        # Get all active recurring transactions that are due
        due_recurring = db.query(RecurringTransaction).filter(
            and_(
                RecurringTransaction.is_active == True,
                RecurringTransaction.next_date <= current_date
            )
        ).all()

        logger.info(f"Found {len(due_recurring)} due recurring transactions")

        for recurring in due_recurring:
            try:
                # Check if end date has passed
                if recurring.end_date and recurring.end_date < current_date:
                    recurring.is_active = False
                    db.commit()
                    continue

                # Auto-create transaction if enabled
                if recurring.auto_add:
                    RecurringScheduler._create_transaction_from_recurring(
                        db, recurring
                    )
                    stats["created_transactions"] += 1

                # Update next_date
                recurring.next_date = RecurringScheduler._calculate_next_date(
                    recurring.next_date, recurring.frequency
                )
                recurring.last_processed = current_date
                db.commit()

                stats["processed"] += 1

            except Exception as e:
                logger.error(f"Error processing recurring transaction {recurring.id}: {e}")
                stats["errors"] += 1
                db.rollback()
                continue

        return stats

    @staticmethod
    def process_bill_reminders(db: Session) -> Dict[str, int]:
        """
        Create reminders for upcoming bills

        This should be called by a scheduled job (e.g., daily cron)

        Args:
            db: Database session

        Returns:
            Dict with processing statistics
        """
        current_date = datetime.utcnow()
        stats = {
            "processed": 0,
            "reminders_created": 0,
            "errors": 0,
        }

        # Get all active recurring transactions (bills)
        active_recurring = db.query(RecurringTransaction).filter(
            RecurringTransaction.is_active == True
        ).all()

        logger.info(f"Checking {len(active_recurring)} recurring transactions for reminders")

        for recurring in active_recurring:
            try:
                # Calculate reminder date
                reminder_date = recurring.next_date - timedelta(days=recurring.remind_days_before)

                # Check if reminder should be sent today
                if reminder_date.date() == current_date.date():
                    # Check if we already sent a reminder for this occurrence
                    existing_reminder = db.query(Notification).filter(
                        and_(
                            Notification.user_id == recurring.user_id,
                            Notification.type == NotificationType.BILL_REMINDER,
                            Notification.extra_data.contains(recurring.id),
                            Notification.created_at >= current_date.replace(hour=0, minute=0, second=0)
                        )
                    ).first()

                    if not existing_reminder:
                        RecurringScheduler._create_bill_reminder(db, recurring)
                        stats["reminders_created"] += 1

                stats["processed"] += 1

            except Exception as e:
                logger.error(f"Error processing bill reminder for {recurring.id}: {e}")
                stats["errors"] += 1
                continue

        return stats

    @staticmethod
    def _create_transaction_from_recurring(
        db: Session, recurring: RecurringTransaction
    ):
        """
        Create a transaction from a recurring template

        Args:
            db: Database session
            recurring: RecurringTransaction object
        """
        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=recurring.user_id,
            type=recurring.type,
            amount=recurring.amount,
            description=f"{recurring.description} (Auto-added)",
            category=recurring.category,
            date=recurring.next_date,
            recurring=True,
            extra_data=f'{{"recurring_id": "{recurring.id}"}}',
        )

        db.add(transaction)
        db.commit()
        logger.info(f"Created transaction from recurring {recurring.id}")

    @staticmethod
    def _create_bill_reminder(db: Session, recurring: RecurringTransaction):
        """
        Create a bill reminder notification

        Args:
            db: Database session
            recurring: RecurringTransaction object
        """
        days_until = (recurring.next_date.date() - datetime.utcnow().date()).days

        if days_until == 0:
            time_text = "today"
        elif days_until == 1:
            time_text = "tomorrow"
        else:
            time_text = f"in {days_until} days"

        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=recurring.user_id,
            type=NotificationType.BILL_REMINDER,
            title=f"Bill Due: {recurring.description}",
            message=f"Your {recurring.description} bill of ${recurring.amount:,.2f} is due {time_text} ({recurring.next_date.strftime('%b %d, %Y')}).",
            status=NotificationStatus.UNREAD,
            priority=2,  # Medium
            action_url=f"/recurring/{recurring.id}",
            extra_data=f'{{"recurring_id": "{recurring.id}", "amount": {recurring.amount}, "due_date": "{recurring.next_date.isoformat()}"}}',
        )

        db.add(notification)
        db.commit()
        logger.info(f"Created bill reminder for recurring {recurring.id}")

    @staticmethod
    def _calculate_next_date(current_date: datetime, frequency: RecurrenceFrequency) -> datetime:
        """
        Calculate the next occurrence date based on frequency

        Args:
            current_date: Current next_date
            frequency: Recurrence frequency

        Returns:
            Next occurrence datetime
        """
        if frequency == RecurrenceFrequency.DAILY:
            return current_date + timedelta(days=1)
        elif frequency == RecurrenceFrequency.WEEKLY:
            return current_date + timedelta(weeks=1)
        elif frequency == RecurrenceFrequency.BIWEEKLY:
            return current_date + timedelta(weeks=2)
        elif frequency == RecurrenceFrequency.MONTHLY:
            # Add one month
            month = current_date.month
            year = current_date.year
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1
            # Handle day overflow (e.g., Jan 31 -> Feb 28)
            try:
                return current_date.replace(month=month, year=year)
            except ValueError:
                # Day doesn't exist in next month, use last day of month
                if month == 2:
                    # February
                    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                        day = 29
                    else:
                        day = 28
                elif month in [4, 6, 9, 11]:
                    day = 30
                else:
                    day = 31
                return current_date.replace(month=month, year=year, day=day)
        elif frequency == RecurrenceFrequency.QUARTERLY:
            # Add 3 months
            month = current_date.month + 3
            year = current_date.year
            while month > 12:
                month -= 12
                year += 1
            try:
                return current_date.replace(month=month, year=year)
            except ValueError:
                # Handle day overflow
                if month == 2:
                    day = 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
                elif month in [4, 6, 9, 11]:
                    day = 30
                else:
                    day = 31
                return current_date.replace(month=month, year=year, day=day)
        elif frequency == RecurrenceFrequency.YEARLY:
            # Add one year
            try:
                return current_date.replace(year=current_date.year + 1)
            except ValueError:
                # Feb 29 leap year handling
                return current_date.replace(year=current_date.year + 1, day=28)
        else:
            # Default to monthly
            return current_date + timedelta(days=30)
