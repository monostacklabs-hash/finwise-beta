"""
Dynamic Budget Adjustment Service
Automatically adjusts budgets based on spending behavior and goals
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from ..database.models import Budget, Transaction, TransactionType, Goal, GoalStatus
from ..database.category_hierarchy import CATEGORY_HIERARCHY
from .budget_tracker import BudgetTracker

logger = logging.getLogger(__name__)


class DynamicBudgetAdjuster:
    """
    Intelligently adjusts budgets based on:
    1. Spending patterns (overspending in one category affects others)
    2. Goal priorities (allocate more to high-priority goals)
    3. Historical trends (seasonal adjustments)
    4. Income changes (scale budgets proportionally)
    """
    
    @staticmethod
    def analyze_and_adjust_budgets(
        db: Session,
        user_id: str,
        current_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Analyze spending patterns and suggest/apply budget adjustments
        
        Args:
            db: Database session
            user_id: User ID
            current_date: Current date (defaults to now)
            
        Returns:
            Dict with analysis and adjustment recommendations
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
        
        if not budgets:
            return {
                "status": "no_budgets",
                "message": "No active budgets to adjust",
                "adjustments": []
            }
        
        # Get budget statuses
        budget_statuses = BudgetTracker.get_all_budget_statuses(db, user_id, current_date)
        
        # Analyze spending patterns
        analysis = DynamicBudgetAdjuster._analyze_spending_patterns(
            db, user_id, budget_statuses, current_date
        )
        
        # Get active goals for priority-based adjustments
        goals = db.query(Goal).filter(
            and_(
                Goal.user_id == user_id,
                Goal.status == GoalStatus.ACTIVE
            )
        ).order_by(Goal.priority.desc()).all()
        
        # Generate adjustment recommendations
        adjustments = DynamicBudgetAdjuster._generate_adjustments(
            budget_statuses, analysis, goals
        )
        
        return {
            "status": "success",
            "analysis": analysis,
            "adjustments": adjustments,
            "total_budgets": len(budgets),
            "overspent_categories": len([b for b in budget_statuses if b["is_overspent"]]),
        }
    
    @staticmethod
    def apply_adjustments(
        db: Session,
        user_id: str,
        adjustments: List[Dict],
        auto_apply: bool = False,
    ) -> Dict:
        """
        Apply budget adjustments
        
        Args:
            db: Database session
            user_id: User ID
            adjustments: List of adjustment recommendations
            auto_apply: If True, apply automatically; if False, return for user approval
            
        Returns:
            Dict with applied adjustments
        """
        applied = []
        
        for adj in adjustments:
            if not auto_apply and adj.get("requires_approval", True):
                continue
            
            budget = db.query(Budget).filter(
                and_(
                    Budget.id == adj["budget_id"],
                    Budget.user_id == user_id
                )
            ).first()
            
            if budget:
                old_amount = budget.amount
                budget.amount = adj["new_amount"]
                budget.updated_at = datetime.utcnow()
                
                applied.append({
                    "category": budget.category,
                    "old_amount": old_amount,
                    "new_amount": adj["new_amount"],
                    "change": adj["new_amount"] - old_amount,
                    "reason": adj["reason"],
                })
        
        if applied:
            db.commit()
            logger.info(f"Applied {len(applied)} budget adjustments for user {user_id}")
        
        return {
            "status": "success",
            "applied_count": len(applied),
            "adjustments": applied,
        }
    
    @staticmethod
    def _analyze_spending_patterns(
        db: Session,
        user_id: str,
        budget_statuses: List[Dict],
        current_date: datetime,
    ) -> Dict:
        """Analyze spending patterns across categories"""
        
        # Calculate total budget and total spent
        total_budget = sum(b["budgeted_amount"] for b in budget_statuses)
        total_spent = sum(b["actual_spent"] for b in budget_statuses)
        
        # Identify problem areas
        overspent_categories = [
            b for b in budget_statuses if b["is_overspent"]
        ]
        
        underspent_categories = [
            b for b in budget_statuses 
            if b["percentage_used"] < 50 and not b["is_overspent"]
        ]
        
        # Calculate spending velocity (trend)
        lookback_days = 30
        lookback_start = current_date - timedelta(days=lookback_days)
        
        recent_spending = db.query(
            func.sum(Transaction.amount)
        ).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.date >= lookback_start,
                Transaction.date < current_date
            )
        ).scalar() or 0
        
        # Calculate daily average
        daily_avg = recent_spending / lookback_days if lookback_days > 0 else 0
        
        # Projected monthly spending
        projected_monthly = daily_avg * 30
        
        return {
            "total_budget": total_budget,
            "total_spent": total_spent,
            "budget_utilization": (total_spent / total_budget * 100) if total_budget > 0 else 0,
            "overspent_categories": len(overspent_categories),
            "underspent_categories": len(underspent_categories),
            "daily_average_spending": round(daily_avg, 2),
            "projected_monthly_spending": round(projected_monthly, 2),
            "overspending_amount": sum(
                b["actual_spent"] - b["budgeted_amount"] 
                for b in overspent_categories
            ),
        }
    
    @staticmethod
    def _generate_adjustments(
        budget_statuses: List[Dict],
        analysis: Dict,
        goals: List[Goal],
    ) -> List[Dict]:
        """
        Generate budget adjustment recommendations
        
        Strategy:
        1. If overspending in one category, reduce discretionary categories
        2. If underspending consistently, reallocate to goals or other needs
        3. Prioritize essential categories (home, healthcare) over discretionary
        """
        adjustments = []
        
        # Define essential vs discretionary categories
        essential_categories = {
            "home", "groceries", "utilities", "healthcare", "transport", "rent_mortgage"
        }
        
        discretionary_categories = {
            "entertainment", "dining_out", "shopping", "coffee_shops", "streaming"
        }
        
        # Find overspent categories
        overspent = [b for b in budget_statuses if b["is_overspent"]]
        
        if overspent:
            # Calculate total overspending
            total_overspend = sum(
                b["actual_spent"] - b["budgeted_amount"] for b in overspent
            )
            
            # Find discretionary categories to reduce
            discretionary_budgets = [
                b for b in budget_statuses
                if CATEGORY_HIERARCHY.get_root_category(b["category"]) in discretionary_categories
                and not b["is_overspent"]
            ]
            
            if discretionary_budgets:
                # Distribute reduction across discretionary categories
                reduction_per_category = total_overspend / len(discretionary_budgets)
                
                for budget in discretionary_budgets:
                    reduction = min(
                        reduction_per_category,
                        budget["budgeted_amount"] * 0.2  # Max 20% reduction
                    )
                    
                    new_amount = budget["budgeted_amount"] - reduction
                    
                    adjustments.append({
                        "budget_id": budget["budget_id"],
                        "category": budget["category"],
                        "current_amount": budget["budgeted_amount"],
                        "new_amount": round(new_amount, 2),
                        "change": round(-reduction, 2),
                        "reason": f"Reducing to compensate for overspending in {', '.join(b['category'] for b in overspent)}",
                        "type": "reduction",
                        "requires_approval": True,
                    })
        
        # Find consistently underspent categories (< 50% usage)
        underspent = [
            b for b in budget_statuses
            if b["percentage_used"] < 50 and not b["is_overspent"]
        ]
        
        for budget in underspent:
            # Suggest reducing budget by 20%
            reduction = budget["budgeted_amount"] * 0.2
            new_amount = budget["budgeted_amount"] - reduction
            
            adjustments.append({
                "budget_id": budget["budget_id"],
                "category": budget["category"],
                "current_amount": budget["budgeted_amount"],
                "new_amount": round(new_amount, 2),
                "change": round(-reduction, 2),
                "reason": f"Only using {budget['percentage_used']:.0f}% of budget - consider reallocating",
                "type": "optimization",
                "requires_approval": True,
            })
        
        # Goal-based adjustments (if high-priority goals exist)
        if goals:
            high_priority_goals = [g for g in goals if g.priority >= 3]
            
            if high_priority_goals:
                # Suggest increasing savings allocation
                for budget in budget_statuses:
                    root_cat = CATEGORY_HIERARCHY.get_root_category(budget["category"])
                    
                    if root_cat in discretionary_categories:
                        # Suggest 10% reduction to fund goals
                        reduction = budget["budgeted_amount"] * 0.1
                        new_amount = budget["budgeted_amount"] - reduction
                        
                        goal_names = ", ".join(g.name for g in high_priority_goals[:2])
                        
                        adjustments.append({
                            "budget_id": budget["budget_id"],
                            "category": budget["category"],
                            "current_amount": budget["budgeted_amount"],
                            "new_amount": round(new_amount, 2),
                            "change": round(-reduction, 2),
                            "reason": f"Reallocate to high-priority goals: {goal_names}",
                            "type": "goal_optimization",
                            "requires_approval": True,
                        })
        
        return adjustments
