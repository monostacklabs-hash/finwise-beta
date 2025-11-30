"""
Debt Optimization Service
"""
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import math


class DebtOptimizer:
    """Optimize debt repayment strategies"""

    @staticmethod
    def calculate_repayment_schedule(
        principal: float,
        annual_interest_rate: float,
        start_date: datetime,
        monthly_payment: float,
        max_months: int = 360,
    ) -> List[Dict]:
        """
        Calculate detailed repayment schedule

        Args:
            principal: Initial loan amount
            annual_interest_rate: Annual interest rate as percentage (e.g., 5.5)
            start_date: Start date of the loan
            monthly_payment: Fixed monthly payment amount
            max_months: Maximum months to calculate (default 360 = 30 years)

        Returns:
            List of payment details for each month
        """
        schedule = []
        remaining_balance = principal
        monthly_rate = annual_interest_rate / 100 / 12
        current_date = start_date

        for month in range(1, max_months + 1):
            if remaining_balance <= 0:
                break

            # Calculate interest for this month
            interest_payment = remaining_balance * monthly_rate
            principal_payment = min(monthly_payment - interest_payment, remaining_balance)

            # Handle case where payment doesn't cover interest
            if principal_payment < 0:
                principal_payment = 0

            remaining_balance -= principal_payment
            current_date = start_date + relativedelta(months=month)

            schedule.append(
                {
                    "month": month,
                    "date": current_date.strftime("%Y-%m-%d"),
                    "payment": round(monthly_payment, 2),
                    "principal": round(principal_payment, 2),
                    "interest": round(interest_payment, 2),
                    "remaining_balance": round(max(0, remaining_balance), 2),
                }
            )

            if remaining_balance <= 0:
                break

        return schedule

    @staticmethod
    def calculate_minimum_payment(
        principal: float, annual_interest_rate: float, months: int
    ) -> float:
        """
        Calculate minimum monthly payment using amortization formula

        Formula: M = P * [r(1 + r)^n] / [(1 + r)^n - 1]
        Where:
            M = monthly payment
            P = principal
            r = monthly interest rate
            n = number of months
        """
        if annual_interest_rate == 0:
            return principal / months

        monthly_rate = annual_interest_rate / 100 / 12
        payment = principal * (
            monthly_rate * math.pow(1 + monthly_rate, months)
        ) / (math.pow(1 + monthly_rate, months) - 1)

        return round(payment, 2)

    @staticmethod
    def optimize_debt_strategy(
        debts: List[Dict], extra_monthly_budget: float
    ) -> Dict:
        """
        Determine optimal debt repayment strategy

        Compares avalanche (highest interest first) vs snowball (smallest balance first)

        Args:
            debts: List of debt objects with id, name, remainingAmount, interestRate, monthlyPayment
            extra_monthly_budget: Extra money available for debt repayment

        Returns:
            Optimization recommendation with both strategies analyzed
        """
        if not debts:
            return {
                "strategy": "none",
                "message": "No debts to optimize",
                "avalanche": None,
                "snowball": None,
            }

        # Calculate avalanche strategy (highest interest first)
        avalanche_result = DebtOptimizer._simulate_strategy(
            debts, extra_monthly_budget, strategy="avalanche"
        )

        # Calculate snowball strategy (smallest balance first)
        snowball_result = DebtOptimizer._simulate_strategy(
            debts, extra_monthly_budget, strategy="snowball"
        )

        # Determine which is better
        avalanche_total_interest = sum(
            d["total_interest"] for d in avalanche_result["debts"]
        )
        snowball_total_interest = sum(
            d["total_interest"] for d in snowball_result["debts"]
        )

        recommended_strategy = (
            "avalanche" if avalanche_total_interest < snowball_total_interest else "snowball"
        )
        savings = abs(avalanche_total_interest - snowball_total_interest)

        return {
            "recommended_strategy": recommended_strategy,
            "avalanche": avalanche_result,
            "snowball": snowball_result,
            "interest_savings": round(savings, 2),
            "summary": f"Using {recommended_strategy} strategy saves ${round(savings, 2)} in interest",
        }

    @staticmethod
    def _simulate_strategy(
        debts: List[Dict], extra_budget: float, strategy: str
    ) -> Dict:
        """Simulate debt repayment with given strategy"""
        # Sort debts based on strategy
        if strategy == "avalanche":
            sorted_debts = sorted(
                debts, key=lambda d: d["interestRate"], reverse=True
            )
        else:  # snowball
            sorted_debts = sorted(debts, key=lambda d: d["remainingAmount"])

        total_months = 0
        total_interest = 0
        debt_results = []

        for debt in sorted_debts:
            remaining = debt["remainingAmount"]
            rate = debt["interestRate"] / 100 / 12
            payment = debt["monthlyPayment"] + extra_budget
            months = 0
            interest_paid = 0

            while remaining > 0 and months < 360:
                interest = remaining * rate
                principal = min(payment - interest, remaining)
                remaining -= principal
                interest_paid += interest
                months += 1

            total_months = max(total_months, months)
            total_interest += interest_paid

            debt_results.append(
                {
                    "id": debt["id"],
                    "name": debt["name"],
                    "months_to_payoff": months,
                    "total_interest": round(interest_paid, 2),
                }
            )

        return {
            "total_months": total_months,
            "total_interest": round(total_interest, 2),
            "debts": debt_results,
        }
