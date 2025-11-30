"""
AI-Enhanced Recurring Transaction Pattern Detector
Uses semantic understanding and ML to detect complex recurring patterns
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging
import json
import os

from ..database.models import Transaction, RecurringTransaction, TransactionType, RecurrenceFrequency
from ..config import settings

logger = logging.getLogger(__name__)


class AIRecurringDetector:
    """AI-enhanced recurring transaction pattern detector"""

    # Base thresholds (can be adjusted per user based on feedback)
    SEMANTIC_SIMILARITY_THRESHOLD = 0.85
    BASE_AMOUNT_TOLERANCE = 0.15  # 15% variance
    UTILITY_AMOUNT_TOLERANCE = 0.30  # 30% for utilities
    MIN_OCCURRENCES = 2
    MIN_CONFIDENCE = 0.60  # Don't show patterns below this
    
    # Pattern detection intervals (in days, with 20% tolerance)
    PATTERN_INTERVALS = {
        "weekly": 7,
        "biweekly": 14,
        "monthly": 30,
        "bimonthly": 60,
        "quarterly": 90,
        "semiannual": 180,
        "annual": 365,
    }

    @staticmethod
    def detect_patterns(db: Session, user_id: str, use_ai: bool = True) -> List[Dict]:
        """
        Analyze user's transactions and detect recurring patterns using AI
        
        Args:
            db: Database session
            user_id: User ID
            use_ai: Whether to use AI enhancement (falls back to statistical if False)
            
        Returns:
            List of detected patterns with confidence scores
        """
        # Get transactions from last 12 months for better seasonal detection
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        transactions = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= twelve_months_ago
            )
            .order_by(Transaction.date)
            .all()
        )

        if len(transactions) < AIRecurringDetector.MIN_OCCURRENCES:
            return []

        logger.info(f"Analyzing {len(transactions)} transactions for recurring patterns")

        # Group similar transactions using semantic similarity
        grouped = AIRecurringDetector._group_similar_transactions_semantic(
            transactions, use_ai=use_ai
        )

        logger.info(f"Found {len(grouped)} potential recurring groups")

        # Analyze each group for patterns
        suggestions = []
        for group in grouped:
            if len(group) >= AIRecurringDetector.MIN_OCCURRENCES:
                pattern = AIRecurringDetector._analyze_pattern_ai(
                    group, use_ai=use_ai
                )
                if pattern and pattern["confidence"] >= AIRecurringDetector.MIN_CONFIDENCE:
                    # Check if already exists
                    existing = AIRecurringDetector._check_existing_recurring(
                        db, user_id, pattern
                    )
                    if not existing:
                        suggestions.append(pattern)

        logger.info(f"Detected {len(suggestions)} new recurring patterns")
        return suggestions

    @staticmethod
    def _normalize_description(description: str) -> str:
        """Normalize transaction description for better matching"""
        # Remove common suffixes
        suffixes = ["INC", "LLC", "CORP", "LTD", "SUBSCRIPTION", "SUB", "PAYMENT", "PMT"]
        desc = description.upper().strip()
        
        for suffix in suffixes:
            if desc.endswith(suffix):
                desc = desc[:-len(suffix)].strip()
        
        return desc

    @staticmethod
    def _calculate_semantic_similarity(desc1: str, desc2: str, use_ai: bool = True) -> float:
        """
        Calculate semantic similarity between two descriptions
        Uses embeddings for AI mode, falls back to word overlap
        """
        if not use_ai:
            return AIRecurringDetector._word_overlap_similarity(desc1, desc2)
        
        try:
            # Normalize descriptions
            norm1 = AIRecurringDetector._normalize_description(desc1)
            norm2 = AIRecurringDetector._normalize_description(desc2)
            
            # Quick exact match check
            if norm1 == norm2:
                return 1.0
            
            # Check if one contains the other
            if norm1 in norm2 or norm2 in norm1:
                return 0.95
            
            # For now, use enhanced word overlap
            # TODO: Implement actual embeddings when needed
            return AIRecurringDetector._word_overlap_similarity(desc1, desc2)
            
        except Exception as e:
            logger.warning(f"Semantic similarity failed, falling back: {e}")
            return AIRecurringDetector._word_overlap_similarity(desc1, desc2)

    @staticmethod
    def _word_overlap_similarity(desc1: str, desc2: str) -> float:
        """Calculate similarity based on word overlap (fallback method)"""
        desc1 = desc1.lower().strip()
        desc2 = desc2.lower().strip()
        
        if desc1 == desc2:
            return 1.0
        
        if desc1 in desc2 or desc2 in desc1:
            return 0.9
        
        words1 = set(desc1.split())
        words2 = set(desc2.split())
        
        if not words1 or not words2:
            return 0.0
        
        overlap = len(words1 & words2)
        union = len(words1 | words2)
        
        return overlap / union if union > 0 else 0.0

    @staticmethod
    def _group_similar_transactions_semantic(
        transactions: List[Transaction],
        use_ai: bool = True
    ) -> List[List[Transaction]]:
        """Group transactions using semantic similarity"""
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

                # Must be same type
                if trans.type != other.type:
                    continue

                # Check semantic similarity
                similarity = AIRecurringDetector._calculate_semantic_similarity(
                    trans.description, other.description, use_ai=use_ai
                )
                
                if similarity >= AIRecurringDetector.SEMANTIC_SIMILARITY_THRESHOLD:
                    # Check amount similarity with adaptive tolerance
                    tolerance = AIRecurringDetector._get_amount_tolerance(trans.category)
                    if AIRecurringDetector._is_amount_similar(
                        trans.amount, other.amount, tolerance
                    ):
                        group.append(other)
                        used.add(j)

            if len(group) >= AIRecurringDetector.MIN_OCCURRENCES:
                groups.append(group)

        return groups

    @staticmethod
    def _get_amount_tolerance(category: Optional[str]) -> float:
        """Get adaptive amount tolerance based on category"""
        # Higher tolerance for variable bills
        variable_categories = ["utilities", "phone", "internet", "electricity", "water", "gas"]
        
        if category and any(cat in category.lower() for cat in variable_categories):
            return AIRecurringDetector.UTILITY_AMOUNT_TOLERANCE
        
        return AIRecurringDetector.BASE_AMOUNT_TOLERANCE

    @staticmethod
    def _is_amount_similar(amount1: float, amount2: float, tolerance: float) -> bool:
        """Check if two amounts are similar within tolerance"""
        if amount1 == 0 or amount2 == 0:
            return amount1 == amount2

        diff = abs(amount1 - amount2)
        avg = (amount1 + amount2) / 2
        return (diff / avg) <= tolerance

    @staticmethod
    def _analyze_pattern_ai(
        transactions: List[Transaction],
        use_ai: bool = True
    ) -> Optional[Dict]:
        """Analyze transaction group to detect recurring pattern using AI"""
        if len(transactions) < 2:
            return None

        # Sort by date
        sorted_trans = sorted(transactions, key=lambda t: t.date)

        # Calculate intervals
        intervals = []
        for i in range(len(sorted_trans) - 1):
            days = (sorted_trans[i + 1].date - sorted_trans[i].date).days
            intervals.append(days)

        if not intervals:
            return None

        # Detect frequency pattern
        frequency, interval_confidence = AIRecurringDetector._detect_frequency_pattern(
            intervals
        )

        if not frequency:
            return None

        # Calculate statistics
        avg_amount = sum(t.amount for t in sorted_trans) / len(sorted_trans)
        amount_variance = AIRecurringDetector._calculate_amount_variance(sorted_trans)
        
        # Get most common values
        descriptions = [t.description for t in sorted_trans]
        most_common_desc = max(set(descriptions), key=descriptions.count)
        
        categories = [t.category for t in sorted_trans]
        most_common_cat = max(set(categories), key=categories.count)

        # Calculate next expected date
        last_date = sorted_trans[-1].date
        next_date, date_range = AIRecurringDetector._predict_next_occurrence(
            last_date, frequency, intervals
        )

        # Calculate overall confidence
        confidence = AIRecurringDetector._calculate_pattern_confidence(
            intervals,
            amount_variance,
            len(sorted_trans),
            interval_confidence
        )

        # Use AI to analyze pattern if enabled and sufficient data
        ai_insights = None
        if use_ai and len(sorted_trans) >= 3:
            ai_insights = AIRecurringDetector._get_ai_pattern_insights(
                sorted_trans, frequency, confidence
            )

        pattern = {
            "transaction_type": sorted_trans[0].type.value,
            "amount": round(avg_amount, 2),
            "amount_variance": round(amount_variance, 2),
            "description": most_common_desc,
            "category": most_common_cat,
            "frequency": frequency,
            "next_date": next_date.strftime("%Y-%m-%d"),
            "date_range": date_range,
            "occurrences": len(sorted_trans),
            "confidence": confidence,
            "confidence_level": AIRecurringDetector._get_confidence_level(confidence),
            "sample_dates": [t.date.strftime("%Y-%m-%d") for t in sorted_trans[-5:]],
            "method": "ai" if use_ai else "statistical",
        }

        if ai_insights:
            pattern["ai_insights"] = ai_insights

        return pattern

    @staticmethod
    def _detect_frequency_pattern(intervals: List[int]) -> Tuple[Optional[str], float]:
        """
        Detect frequency pattern from intervals
        Returns (frequency, confidence)
        """
        if not intervals:
            return None, 0.0

        avg_interval = sum(intervals) / len(intervals)
        
        # Try to match to known patterns (with 20% tolerance)
        tolerance = 0.20
        best_match = None
        best_confidence = 0.0

        for freq_name, expected_days in AIRecurringDetector.PATTERN_INTERVALS.items():
            min_days = expected_days * (1 - tolerance)
            max_days = expected_days * (1 + tolerance)

            if min_days <= avg_interval <= max_days:
                # Calculate how close to expected
                deviation = abs(avg_interval - expected_days) / expected_days
                match_confidence = 1.0 - deviation
                
                if match_confidence > best_confidence:
                    best_match = freq_name
                    best_confidence = match_confidence

        return best_match, best_confidence

    @staticmethod
    def _calculate_amount_variance(transactions: List[Transaction]) -> float:
        """Calculate amount variance as percentage"""
        if len(transactions) < 2:
            return 0.0

        amounts = [t.amount for t in transactions]
        avg = sum(amounts) / len(amounts)
        
        if avg == 0:
            return 0.0

        variance = sum((amt - avg) ** 2 for amt in amounts) / len(amounts)
        std_dev = variance ** 0.5
        
        return (std_dev / avg) * 100  # Return as percentage

    @staticmethod
    def _predict_next_occurrence(
        last_date: datetime,
        frequency: str,
        intervals: List[int]
    ) -> Tuple[datetime, Optional[str]]:
        """
        Predict next occurrence date with confidence range
        Returns (predicted_date, date_range_string)
        """
        expected_days = AIRecurringDetector.PATTERN_INTERVALS.get(frequency, 30)
        next_date = last_date + timedelta(days=expected_days)

        # Calculate variance in intervals
        if len(intervals) > 1:
            avg_interval = sum(intervals) / len(intervals)
            variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
            std_dev = variance ** 0.5

            # If high variance, provide date range
            if std_dev > avg_interval * 0.15:  # More than 15% variance
                range_days = int(std_dev)
                date_range = f"{(next_date - timedelta(days=range_days)).strftime('%Y-%m-%d')} to {(next_date + timedelta(days=range_days)).strftime('%Y-%m-%d')}"
                return next_date, date_range

        return next_date, None

    @staticmethod
    def _calculate_pattern_confidence(
        intervals: List[int],
        amount_variance: float,
        occurrence_count: int,
        interval_confidence: float
    ) -> float:
        """
        Calculate overall pattern confidence score (0-1)
        Considers interval consistency, amount consistency, and occurrence count
        """
        # Interval consistency (from frequency detection)
        interval_score = interval_confidence

        # Amount consistency (lower variance = higher score)
        # 0% variance = 1.0, 30% variance = 0.0
        amount_score = max(0, 1.0 - (amount_variance / 30.0))

        # Occurrence count bonus (more occurrences = higher confidence)
        # 2 occurrences = 0.5, 5+ occurrences = 1.0
        occurrence_score = min(1.0, (occurrence_count - 2) / 3 + 0.5)

        # Weighted average
        confidence = (
            interval_score * 0.4 +
            amount_score * 0.3 +
            occurrence_score * 0.3
        )

        return round(confidence, 2)

    @staticmethod
    def _get_confidence_level(confidence: float) -> str:
        """Convert confidence score to human-readable level"""
        if confidence >= 0.9:
            return "high"
        elif confidence >= 0.75:
            return "medium"
        elif confidence >= 0.6:
            return "low"
        else:
            return "very_low"

    @staticmethod
    def _get_ai_pattern_insights(
        transactions: List[Transaction],
        frequency: str,
        confidence: float
    ) -> Optional[str]:
        """
        Use AI to provide natural language insights about the pattern
        """
        try:
            # Check if AI is available
            if not settings.AI_PROVIDER:
                return None

            # Build context
            sorted_trans = sorted(transactions, key=lambda t: t.date)
            amounts = [t.amount for t in sorted_trans]
            dates = [t.date.strftime("%Y-%m-%d") for t in sorted_trans]
            
            prompt = f"""Analyze this recurring transaction pattern and provide a brief insight (1-2 sentences):

Merchant: {sorted_trans[0].description}
Category: {sorted_trans[0].category}
Frequency: {frequency}
Occurrences: {len(transactions)}
Amounts: {amounts}
Dates: {dates}
Confidence: {confidence}

Provide a helpful insight about this pattern. Is it consistent? Any trends? Any recommendations?
Keep it brief and actionable."""

            # Initialize LLM based on provider
            from langchain_anthropic import ChatAnthropic
            from langchain_openai import ChatOpenAI
            
            provider = getattr(settings, 'AI_PROVIDER', 'anthropic').lower()
            model = settings.get_model_for_provider(provider)
            
            if provider in ["anthropic", "claude"] and settings.ANTHROPIC_API_KEY:
                llm = ChatAnthropic(
                    api_key=settings.ANTHROPIC_API_KEY,
                    model=model,
                    temperature=0.3,
                    max_tokens=150,
                )
            elif settings.OPENAI_API_KEY:
                llm = ChatOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    model=model,
                    temperature=0.3,
                    max_tokens=150,
                )
            else:
                return None

            # Get response
            response = llm.invoke(prompt)
            insight = response.content.strip()
            return insight

        except Exception as e:
            logger.warning(f"AI insights failed: {e}")
            return None

    @staticmethod
    def _check_existing_recurring(
        db: Session, user_id: str, pattern: Dict
    ) -> bool:
        """Check if recurring transaction already exists for this pattern"""
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

    @staticmethod
    def check_new_transaction_for_pattern(
        db: Session,
        user_id: str,
        new_transaction: Transaction,
        use_ai: bool = True
    ) -> Optional[Dict]:
        """
        Check if a newly added transaction matches an existing pattern
        """
        # Look for similar transactions in the past year
        similar = AIRecurringDetector._find_similar_transactions(
            db, user_id, new_transaction, days_back=365, use_ai=use_ai
        )

        if len(similar) >= 1:
            # Add new transaction to group
            group = similar + [new_transaction]
            pattern = AIRecurringDetector._analyze_pattern_ai(group, use_ai=use_ai)

            if pattern and pattern["confidence"] >= AIRecurringDetector.MIN_CONFIDENCE:
                # Check if already exists
                existing = AIRecurringDetector._check_existing_recurring(
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
        days_back: int = 365,
        use_ai: bool = True
    ) -> List[Transaction]:
        """Find transactions similar to reference using semantic matching"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Get adaptive tolerance
        tolerance = AIRecurringDetector._get_amount_tolerance(reference.category)
        amount_min = reference.amount * (1 - tolerance)
        amount_max = reference.amount * (1 + tolerance)

        # Get candidates
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

        # Filter by semantic similarity
        similar = []
        for candidate in candidates:
            similarity = AIRecurringDetector._calculate_semantic_similarity(
                reference.description, candidate.description, use_ai=use_ai
            )
            if similarity >= AIRecurringDetector.SEMANTIC_SIMILARITY_THRESHOLD:
                similar.append(candidate)

        return similar
