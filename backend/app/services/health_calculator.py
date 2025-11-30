"""
Financial Health Calculation Service
"""
from typing import Dict, List
from datetime import datetime
from ..database.models import Transaction, DebtLoan, Goal


class HealthCalculator:
    """Calculate comprehensive financial health metrics"""

    @staticmethod
    def calculate_health_metrics(
        total_income: float,
        total_expenses: float,
        total_debt: float,
        total_assets: float,
    ) -> Dict:
        """
        Calculate comprehensive financial health metrics

        Returns:
            Dictionary with health metrics including net worth, ratios, and health score
        """
        net_worth = total_assets - total_debt
        savings_rate = (
            ((total_income - total_expenses) / total_income * 100)
            if total_income > 0
            else 0
        )
        debt_ratio = (total_debt / total_assets * 100) if total_assets > 0 else 0
        liquidity_ratio = (
            total_assets / total_debt
            if total_debt > 0
            else (10 if total_assets > 0 else 0)
        )

        # Calculate health score (0-100)
        health_score = HealthCalculator._calculate_health_score(
            savings_rate, debt_ratio, liquidity_ratio, net_worth
        )

        return {
            "net_worth": round(net_worth, 2),
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "total_debt": round(total_debt, 2),
            "total_assets": round(total_assets, 2),
            "savings_rate": round(savings_rate, 2),
            "debt_ratio": round(debt_ratio, 2),
            "liquidity_ratio": round(liquidity_ratio, 2),
            "health_score": health_score,
        }

    @staticmethod
    def _calculate_health_score(
        savings_rate: float, debt_ratio: float, liquidity_ratio: float, net_worth: float
    ) -> int:
        """Calculate overall health score based on multiple factors"""
        score = 50  # Base score

        # Savings rate impact (+/-25 points)
        if savings_rate > 20:
            score += 25
        elif savings_rate > 10:
            score += 15
        elif savings_rate > 5:
            score += 10
        elif savings_rate < 0:
            score -= 10

        # Debt ratio impact (+/-25 points)
        if debt_ratio < 20:
            score += 25
        elif debt_ratio < 40:
            score += 15
        elif debt_ratio < 60:
            score += 5
        else:
            score -= 15

        # Liquidity ratio impact (+/-25 points)
        if liquidity_ratio > 3:
            score += 25
        elif liquidity_ratio > 2:
            score += 15
        elif liquidity_ratio > 1:
            score += 10
        else:
            score -= 10

        # Net worth impact (+/-25 points)
        if net_worth > 50000:
            score += 25
        elif net_worth > 10000:
            score += 15
        elif net_worth > 0:
            score += 5
        elif net_worth < -10000:
            score -= 25
        else:
            score -= 10

        return max(0, min(100, score))

    @staticmethod
    def categorize_health_score(score: int) -> str:
        """Categorize health score into descriptive levels"""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        elif score >= 20:
            return "Poor"
        else:
            return "Critical"
