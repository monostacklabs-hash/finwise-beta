"""
Goal Projection Service
"""
from typing import Dict
from datetime import datetime
from dateutil.relativedelta import relativedelta


class GoalProjector:
    """Project financial goal achievement"""

    @staticmethod
    def calculate_goal_projection(
        target_amount: float,
        current_amount: float,
        target_date: datetime,
        monthly_income: float,
        monthly_expenses: float,
    ) -> Dict:
        """
        Project goal achievement timeline

        Args:
            target_amount: Target goal amount
            current_amount: Current saved amount
            target_date: Target achievement date
            monthly_income: Monthly income
            monthly_expenses: Monthly expenses

        Returns:
            Projection with status, required contributions, and probability
        """
        now = datetime.utcnow()

        # Calculate months remaining
        months_remaining = (
            (target_date.year - now.year) * 12 + (target_date.month - now.month)
        )
        months_remaining = max(0, months_remaining)

        # Calculate what's needed
        remaining_amount = target_amount - current_amount
        monthly_contribution_needed = (
            remaining_amount / months_remaining if months_remaining > 0 else remaining_amount
        )

        # Calculate available monthly surplus
        available_monthly = monthly_income - monthly_expenses

        # Determine status
        status = GoalProjector._determine_status(
            current_amount, target_amount, monthly_contribution_needed, available_monthly
        )

        # Calculate estimated completion
        estimated_months = (
            math.ceil(remaining_amount / available_monthly)
            if available_monthly > 0
            else 999
        )
        estimated_completion = now + relativedelta(months=estimated_months)

        # Calculate probability of achievement
        probability = GoalProjector._calculate_probability(
            monthly_contribution_needed, available_monthly
        )

        return {
            "target_amount": round(target_amount, 2),
            "current_amount": round(current_amount, 2),
            "remaining_amount": round(remaining_amount, 2),
            "target_date": target_date.strftime("%Y-%m-%d"),
            "months_remaining": months_remaining,
            "monthly_contribution_needed": round(monthly_contribution_needed, 2),
            "available_monthly": round(available_monthly, 2),
            "estimated_completion": estimated_completion.strftime("%Y-%m-%d"),
            "estimated_months": estimated_months,
            "status": status,
            "probability": probability,
            "on_track": status in ["on-track", "achieved"],
        }

    @staticmethod
    def _determine_status(
        current: float, target: float, needed: float, available: float
    ) -> str:
        """Determine goal status"""
        if current >= target:
            return "achieved"
        elif needed > available * 1.2:
            return "behind"
        elif needed > available:
            return "at-risk"
        else:
            return "on-track"

    @staticmethod
    def _calculate_probability(needed: float, available: float) -> float:
        """Calculate probability of achieving goal on time"""
        if available <= 0:
            return 0.1

        ratio = available / needed if needed > 0 else 10

        if ratio >= 1.2:
            return 0.95
        elif ratio >= 1.0:
            return 0.85
        elif ratio >= 0.8:
            return 0.70
        elif ratio >= 0.6:
            return 0.50
        elif ratio >= 0.4:
            return 0.30
        else:
            return 0.15


import math
