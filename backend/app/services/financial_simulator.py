"""
Financial Simulation Engine
Runs "what-if" scenarios for financial planning
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from copy import deepcopy

from ..database.models import Transaction, TransactionType, RecurringTransaction, Budget, Goal
from .cashflow_forecaster import CashFlowForecaster

logger = logging.getLogger(__name__)


class FinancialSimulator:
    """
    Run financial simulations to answer "what-if" questions:
    - What if I increase my savings by $500/month?
    - What if I cut my dining budget by 30%?
    - What if I get a raise?
    - What if I take on a new loan?
    """
    
    @staticmethod
    def simulate_scenario(
        db: Session,
        user_id: str,
        scenario_type: str,
        parameters: Dict,
        forecast_days: int = 180,
        current_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Run a financial simulation scenario
        
        Args:
            db: Database session
            user_id: User ID
            scenario_type: Type of scenario (income_change, expense_change, new_goal, etc.)
            parameters: Scenario-specific parameters
            forecast_days: Days to simulate (default 180)
            current_date: Current date (defaults to now)
            
        Returns:
            Dict with baseline vs scenario comparison
        """
        if current_date is None:
            current_date = datetime.utcnow()
        
        # Get current balance (from parameters or calculate)
        starting_balance = parameters.get("starting_balance", 10000)  # Default
        
        # Run baseline forecast (current state)
        baseline = CashFlowForecaster.forecast_balance(
            db, user_id, starting_balance, forecast_days, current_date
        )
        
        # Run scenario forecast based on type
        if scenario_type == "income_change":
            scenario = FinancialSimulator._simulate_income_change(
                db, user_id, starting_balance, parameters, forecast_days, current_date
            )
        elif scenario_type == "expense_change":
            scenario = FinancialSimulator._simulate_expense_change(
                db, user_id, starting_balance, parameters, forecast_days, current_date
            )
        elif scenario_type == "budget_cut":
            scenario = FinancialSimulator._simulate_budget_cut(
                db, user_id, starting_balance, parameters, forecast_days, current_date
            )
        elif scenario_type == "new_recurring":
            scenario = FinancialSimulator._simulate_new_recurring(
                db, user_id, starting_balance, parameters, forecast_days, current_date
            )
        elif scenario_type == "goal_acceleration":
            scenario = FinancialSimulator._simulate_goal_acceleration(
                db, user_id, starting_balance, parameters, forecast_days, current_date
            )
        else:
            raise ValueError(f"Unknown scenario type: {scenario_type}")
        
        # Compare baseline vs scenario
        comparison = FinancialSimulator._compare_scenarios(baseline, scenario)
        
        return {
            "scenario_type": scenario_type,
            "parameters": parameters,
            "forecast_days": forecast_days,
            "baseline": {
                "ending_balance": baseline["daily_balances"][-1]["balance"],
                "total_income": sum(d["income"] for d in baseline["daily_balances"]),
                "total_expenses": sum(d["expenses"] for d in baseline["daily_balances"]),
                "runway_days": baseline["runway_days"],
            },
            "scenario": {
                "ending_balance": scenario["daily_balances"][-1]["balance"],
                "total_income": sum(d["income"] for d in scenario["daily_balances"]),
                "total_expenses": sum(d["expenses"] for d in scenario["daily_balances"]),
                "runway_days": scenario["runway_days"],
            },
            "comparison": comparison,
            "recommendation": FinancialSimulator._generate_recommendation(comparison, scenario_type),
        }
    
    @staticmethod
    def _simulate_income_change(
        db: Session,
        user_id: str,
        starting_balance: float,
        parameters: Dict,
        forecast_days: int,
        current_date: datetime,
    ) -> Dict:
        """
        Simulate income change (raise, new job, side hustle)
        
        Parameters:
            - change_amount: Monthly income change (positive or negative)
            - change_type: "fixed" or "percentage"
        """
        change_amount = parameters.get("change_amount", 0)
        change_type = parameters.get("change_type", "fixed")
        
        # Get baseline forecast
        baseline = CashFlowForecaster.forecast_balance(
            db, user_id, starting_balance, forecast_days, current_date
        )
        
        # Adjust income in daily balances
        daily_income_change = change_amount / 30  # Convert monthly to daily
        
        modified_balances = []
        current_balance = starting_balance
        
        for day in baseline["daily_balances"]:
            if change_type == "percentage":
                adjusted_income = day["income"] * (1 + change_amount / 100)
            else:
                adjusted_income = day["income"] + daily_income_change
            
            current_balance = current_balance + adjusted_income - day["expenses"]
            
            modified_balances.append({
                "date": day["date"],
                "balance": round(current_balance, 2),
                "income": round(adjusted_income, 2),
                "expenses": day["expenses"],
                "net": round(adjusted_income - day["expenses"], 2),
            })
        
        # Calculate runway
        runway_days = None
        for i, day in enumerate(modified_balances):
            if day["balance"] <= 0:
                runway_days = i
                break
        if runway_days is None:
            runway_days = forecast_days + 1
        
        return {
            "daily_balances": modified_balances,
            "runway_days": runway_days,
        }
    
    @staticmethod
    def _simulate_expense_change(
        db: Session,
        user_id: str,
        starting_balance: float,
        parameters: Dict,
        forecast_days: int,
        current_date: datetime,
    ) -> Dict:
        """
        Simulate expense change (spending reduction/increase)
        
        Parameters:
            - change_amount: Monthly expense change
            - category: Optional category to target
        """
        change_amount = parameters.get("change_amount", 0)
        
        baseline = CashFlowForecaster.forecast_balance(
            db, user_id, starting_balance, forecast_days, current_date
        )
        
        daily_expense_change = change_amount / 30
        
        modified_balances = []
        current_balance = starting_balance
        
        for day in baseline["daily_balances"]:
            adjusted_expenses = max(0, day["expenses"] + daily_expense_change)
            current_balance = current_balance + day["income"] - adjusted_expenses
            
            modified_balances.append({
                "date": day["date"],
                "balance": round(current_balance, 2),
                "income": day["income"],
                "expenses": round(adjusted_expenses, 2),
                "net": round(day["income"] - adjusted_expenses, 2),
            })
        
        runway_days = None
        for i, day in enumerate(modified_balances):
            if day["balance"] <= 0:
                runway_days = i
                break
        if runway_days is None:
            runway_days = forecast_days + 1
        
        return {
            "daily_balances": modified_balances,
            "runway_days": runway_days,
        }
    
    @staticmethod
    def _simulate_budget_cut(
        db: Session,
        user_id: str,
        starting_balance: float,
        parameters: Dict,
        forecast_days: int,
        current_date: datetime,
    ) -> Dict:
        """
        Simulate cutting a specific budget category
        
        Parameters:
            - category: Category to cut
            - reduction_percentage: Percentage to reduce (e.g., 30 for 30%)
        """
        category = parameters.get("category", "")
        reduction_pct = parameters.get("reduction_percentage", 0) / 100
        
        # This is simplified - in reality, we'd need to track category-specific spending
        # For now, apply overall expense reduction
        monthly_reduction = parameters.get("estimated_monthly_savings", 0)
        
        return FinancialSimulator._simulate_expense_change(
            db, user_id, starting_balance,
            {"change_amount": -monthly_reduction},
            forecast_days, current_date
        )
    
    @staticmethod
    def _simulate_new_recurring(
        db: Session,
        user_id: str,
        starting_balance: float,
        parameters: Dict,
        forecast_days: int,
        current_date: datetime,
    ) -> Dict:
        """
        Simulate adding a new recurring transaction
        
        Parameters:
            - amount: Transaction amount
            - frequency: daily, weekly, monthly, etc.
            - type: income or expense
        """
        amount = parameters.get("amount", 0)
        frequency = parameters.get("frequency", "monthly")
        trans_type = parameters.get("type", "expense")
        
        # Convert to daily amount
        frequency_map = {
            "daily": 1,
            "weekly": 7,
            "biweekly": 14,
            "monthly": 30,
            "quarterly": 90,
            "yearly": 365,
        }
        
        days_between = frequency_map.get(frequency, 30)
        
        baseline = CashFlowForecaster.forecast_balance(
            db, user_id, starting_balance, forecast_days, current_date
        )
        
        modified_balances = []
        current_balance = starting_balance
        
        for i, day in enumerate(baseline["daily_balances"]):
            # Add recurring transaction on appropriate days
            extra_income = 0
            extra_expense = 0
            
            if i % days_between == 0:
                if trans_type == "income":
                    extra_income = amount
                else:
                    extra_expense = amount
            
            adjusted_income = day["income"] + extra_income
            adjusted_expenses = day["expenses"] + extra_expense
            
            current_balance = current_balance + adjusted_income - adjusted_expenses
            
            modified_balances.append({
                "date": day["date"],
                "balance": round(current_balance, 2),
                "income": round(adjusted_income, 2),
                "expenses": round(adjusted_expenses, 2),
                "net": round(adjusted_income - adjusted_expenses, 2),
            })
        
        runway_days = None
        for i, day in enumerate(modified_balances):
            if day["balance"] <= 0:
                runway_days = i
                break
        if runway_days is None:
            runway_days = forecast_days + 1
        
        return {
            "daily_balances": modified_balances,
            "runway_days": runway_days,
        }
    
    @staticmethod
    def _simulate_goal_acceleration(
        db: Session,
        user_id: str,
        starting_balance: float,
        parameters: Dict,
        forecast_days: int,
        current_date: datetime,
    ) -> Dict:
        """
        Simulate accelerating a goal by increasing monthly contributions
        
        Parameters:
            - additional_monthly_contribution: Extra amount per month
        """
        additional = parameters.get("additional_monthly_contribution", 0)
        
        # Treat as expense increase
        return FinancialSimulator._simulate_expense_change(
            db, user_id, starting_balance,
            {"change_amount": additional},
            forecast_days, current_date
        )
    
    @staticmethod
    def _compare_scenarios(baseline: Dict, scenario: Dict) -> Dict:
        """Compare baseline vs scenario"""
        baseline_end = baseline["daily_balances"][-1]["balance"]
        scenario_end = scenario["daily_balances"][-1]["balance"]
        
        balance_diff = scenario_end - baseline_end
        runway_diff = scenario["runway_days"] - baseline["runway_days"]
        
        return {
            "balance_difference": round(balance_diff, 2),
            "balance_change_percentage": round((balance_diff / baseline_end * 100) if baseline_end != 0 else 0, 2),
            "runway_difference_days": runway_diff,
            "is_improvement": balance_diff > 0,
        }
    
    @staticmethod
    def _generate_recommendation(comparison: Dict, scenario_type: str) -> str:
        """Generate recommendation based on comparison"""
        if comparison["is_improvement"]:
            return f"✅ This scenario improves your financial position by ${comparison['balance_difference']:,.2f} over the forecast period. Consider implementing this change."
        else:
            return f"⚠️ This scenario would reduce your balance by ${abs(comparison['balance_difference']):,.2f}. Proceed with caution or look for alternatives."
