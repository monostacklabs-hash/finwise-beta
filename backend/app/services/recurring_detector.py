"""
Recurring Transaction Pattern Detector
Analyzes transaction history to detect recurring patterns and suggest automation
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database.models import Transaction, RecurringTransaction, TransactionType, RecurrenceFrequency


class RecurringDetector:
    """Detects recurring transaction patterns from transaction history"""

    # Similarity thresholds
    AMOUNT_TOLERANCE = 0.10  # 10% variance allowed
    DESCRIPTION_SIMILARITY_THRESHOLD = 0.7
    MIN_OCCURRENCES = 2  # Minimum occurrences to suggest recurring

    @staticmethod
    def detect_patterns(db: Session, user_id: str) -> List[Dict]:
        """
        Analyze user's transactions and detect recurring patterns
        Returns list of suggested recurring transactions
        """
        # Get all transactions from the last 6 months
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        transactions = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= six_months_ago
            )
            .order_by(Transaction.date)
            .all()
        )

        if len(transactions) < 2:
            return []

        # Group similar transactions
        grouped = RecurringDetector._group_similar_transactions(transactions)

        # Analyze each group for recurring patterns
        suggestions = []
        for group in grouped:
            if len(group) >= RecurringDetector.MIN_OCCURRENCES:
                pattern = RecurringDetector._analyze_pattern(group)
                if pattern:
                    # Check if already exists as recurring
                    existing = RecurringDetector._check_existing_recurring(
                        db, user_id, pattern
                    )
                    if not existing:
                        suggestions.append(pattern)

        return suggestions

    @staticmethod
    def check_new_transaction_for_pattern(
        db: Session, user_id: str, new_transaction: Transaction
    ) -> Optional[Dict]:
        """
        Check if a newly added transaction matches an existing pattern
        Returns suggestion if pattern detected, None otherwise
        """
        # Look for similar transactions in the past
        similar = RecurringDetector._find_similar_transactions(
            db, user_id, new_transaction, days_back=180
        )

        if len(similar) >= 1:  # At least one previous similar transaction
            # Add the new transaction to the group
            group = similar + [new_transaction]
            pattern = RecurringDetector._analyze_pattern(group)

            if pattern:
                # Check if already exists as recurring
                existing = RecurringDetector._check_existing_recurring(
                    db, user_id, pattern
                )
                if not existing:
                    return pattern

        return None

    @staticmethod
    def _find_similar_transactions(
        db: Session,
        user_id: str,
        reference: Transaction,
        days_back: int = 180
    ) -> List[Transaction]:
        """Find transactions similar to the reference transaction"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Get transactions of same type and similar amount
        amount_min = reference.amount * (1 - RecurringDetector.AMOUNT_TOLERANCE)
        amount_max = reference.amount * (1 + RecurringDetector.AMOUNT_TOLERANCE)

        candidates = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.id != reference.id,
                Transaction.type == reference.type,
                Transaction.amount >= amount_min,
                Transaction.amount <= amount_max,
                Transaction.date >= cutoff_date
            )
            .all()
        )

        # Filter by description similarity
        similar = []
        for candidate in candidates:
            if RecurringDetector._is_description_similar(
                reference.description, candidate.description
            ):
                similar.append(candidate)

        return similar

    @staticmethod
    def _group_similar_transactions(transactions: List[Transaction]) -> List[List[Transaction]]:
        """Group transactions that appear to be recurring"""
        groups = []
        used = set()

        for i, trans in enumerate(transactions):
            if i in used:
                continue

            group = [trans]
            used.add(i)

            # Find similar transactions
            for j, other in enumerate(transactions[i + 1:], start=i + 1):
                if j in used:
                    continue

                # Check if similar
                if (
                    trans.type == other.type
                    and RecurringDetector._is_amount_similar(trans.amount, other.amount)
                    and RecurringDetector._is_description_similar(
                        trans.description, other.description
                    )
                ):
                    group.append(other)
                    used.add(j)

            if len(group) >= RecurringDetector.MIN_OCCURRENCES:
                groups.append(group)

        return groups

    @staticmethod
    def _is_amount_similar(amount1: float, amount2: float) -> bool:
        """Check if two amounts are similar within tolerance"""
        if amount1 == 0 or amount2 == 0:
            return amount1 == amount2

        diff = abs(amount1 - amount2)
        avg = (amount1 + amount2) / 2
        return (diff / avg) <= RecurringDetector.AMOUNT_TOLERANCE

    @staticmethod
    def _is_description_similar(desc1: str, desc2: str) -> bool:
        """Check if two descriptions are similar"""
        desc1 = desc1.lower().strip()
        desc2 = desc2.lower().strip()

        # Exact match
        if desc1 == desc2:
            return True

        # Check if one contains the other (for variations like "Netflix" vs "Netflix subscription")
        if desc1 in desc2 or desc2 in desc1:
            return True

        # Simple word overlap check
        words1 = set(desc1.split())
        words2 = set(desc2.split())
        
        if not words1 or not words2:
            return False

        overlap = len(words1 & words2)
        min_words = min(len(words1), len(words2))

        return (overlap / min_words) >= RecurringDetector.DESCRIPTION_SIMILARITY_THRESHOLD

    @staticmethod
    def _analyze_pattern(transactions: List[Transaction]) -> Optional[Dict]:
        """Analyze a group of transactions to determine recurring pattern"""
        if len(transactions) < 2:
            return None

        # Sort by date
        sorted_trans = sorted(transactions, key=lambda t: t.date)

        # Calculate intervals between transactions
        intervals = []
        for i in range(len(sorted_trans) - 1):
            days = (sorted_trans[i + 1].date - sorted_trans[i].date).days
            intervals.append(days)

        if not intervals:
            return None

        # Determine frequency based on average interval
        avg_interval = sum(intervals) / len(intervals)
        frequency = RecurringDetector._determine_frequency(avg_interval)

        if not frequency:
            return None

        # Calculate average amount
        avg_amount = sum(t.amount for t in sorted_trans) / len(sorted_trans)

        # Use most common description
        descriptions = [t.description for t in sorted_trans]
        most_common_desc = max(set(descriptions), key=descriptions.count)

        # Use most common category
        categories = [t.category for t in sorted_trans]
        most_common_cat = max(set(categories), key=categories.count)

        # Calculate next expected date
        last_date = sorted_trans[-1].date
        next_date = RecurringDetector._calculate_next_date(last_date, frequency)

        return {
            "transaction_type": sorted_trans[0].type.value,
            "amount": round(avg_amount, 2),
            "description": most_common_desc,
            "category": most_common_cat,
            "frequency": frequency,
            "next_date": next_date.strftime("%Y-%m-%d"),
            "occurrences": len(sorted_trans),
            "confidence": RecurringDetector._calculate_confidence(intervals, avg_interval),
            "sample_dates": [t.date.strftime("%Y-%m-%d") for t in sorted_trans[-3:]],
        }

    @staticmethod
    def _determine_frequency(avg_days: float) -> Optional[str]:
        """Determine recurrence frequency from average interval"""
        # Allow 20% tolerance
        tolerance = 0.20

        frequencies = {
            "daily": 1,
            "weekly": 7,
            "biweekly": 14,
            "monthly": 30,
            "quarterly": 90,
            "yearly": 365,
        }

        for freq_name, expected_days in frequencies.items():
            min_days = expected_days * (1 - tolerance)
            max_days = expected_days * (1 + tolerance)

            if min_days <= avg_days <= max_days:
                return freq_name

        return None

    @staticmethod
    def _calculate_next_date(last_date: datetime, frequency: str) -> datetime:
        """Calculate next expected date based on frequency"""
        days_map = {
            "daily": 1,
            "weekly": 7,
            "biweekly": 14,
            "monthly": 30,
            "quarterly": 90,
            "yearly": 365,
        }

        days = days_map.get(frequency, 30)
        return last_date + timedelta(days=days)

    @staticmethod
    def _calculate_confidence(intervals: List[int], avg_interval: float) -> float:
        """Calculate confidence score based on interval consistency"""
        if not intervals or avg_interval == 0:
            return 0.0

        # Calculate variance
        variance = sum((interval - avg_interval) ** 2 for interval in intervals) / len(intervals)
        std_dev = variance ** 0.5

        # Lower variance = higher confidence
        # Normalize to 0-1 scale
        coefficient_of_variation = std_dev / avg_interval if avg_interval > 0 else 1
        confidence = max(0, 1 - coefficient_of_variation)

        return round(confidence, 2)

    @staticmethod
    def _check_existing_recurring(
        db: Session, user_id: str, pattern: Dict
    ) -> bool:
        """Check if a recurring transaction already exists for this pattern"""
        existing = (
            db.query(RecurringTransaction)
            .filter(
                RecurringTransaction.user_id == user_id,
                RecurringTransaction.is_active == True,
                RecurringTransaction.description.ilike(f"%{pattern['description']}%")
            )
            .first()
        )

        return existing is not None
