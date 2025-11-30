"""
AI-Adjusted Goal Milestone Service
Dynamically adjusts goal milestones based on spending patterns and progress
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from dateutil.relativedelta import relativedelta

from ..database.models import Goal, GoalStatus, Transaction, TransactionType

logger = logging.getLogger(__name__)


class GoalMilestoneAdjuster:
    """
    Intelligently adjusts goal milestones based on:
    1. Current progress vs timeline
    2. Recent savings rate
    3. Spending patterns
    4. Income stability
    """
    
    # Milestone percentages
    MILESTONES = [0.25, 0.50, 0.75, 1.0]  # 25%, 50%, 75%, 100%
    
    @staticmethod
    def calculate_adaptive_milestones(
        db: Session,
        user_id: str,
        goal_id: str,
        current_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Calculate adaptive milestones for a goal based on current progress
        
        Args:
            db: Database session
            user_id: User ID
            goal_id: Goal ID
            current_date: Current date (defaults to now)
            
        Returns:
            Dict with milestone dates, amounts, and recommendations
        """
        if current_date is None:
            current_date = datetime.utcnow()
        
        # Get goal
        goal = db.query(Goal).filter(
            and_(
                Goal.id == goal_id,
                Goal.user_id == user_id
            )
        ).first()
        
        if not goal:
            raise ValueError("Goal not found")
        
        # Calculate current progress
        progress_pct = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
        remaining_amount = goal.target_amount - goal.current_amount
        
        # Calculate time remaining
        days_remaining = (goal.target_date - current_date).days
        months_remaining = max(1, days_remaining / 30)
        
        # Analyze recent savings rate
        savings_analysis = GoalMilestoneAdjuster._analyze_savings_rate(
            db, user_id, current_date
        )
        
        # Calculate required monthly contribution
        required_monthly = remaining_amount / months_remaining if months_remaining > 0 else remaining_amount
        
        # Determine if on track
        on_track = savings_analysis["monthly_savings"] >= required_monthly
        
        # Generate adaptive milestones
        milestones = GoalMilestoneAdjuster._generate_milestones(
            goal, current_date, savings_analysis, on_track
        )
        
        # Generate recommendations
        recommendations = GoalMilestoneAdjuster._generate_recommendations(
            goal, savings_analysis, required_monthly, on_track
        )
        
        return {
            "goal_id": goal.id,
            "goal_name": goal.name,
            "target_amount": goal.target_amount,
            "current_amount": goal.current_amount,
            "progress_percentage": round(progress_pct, 2),
            "remaining_amount": round(remaining_amount, 2),
            "days_remaining": days_remaining,
            "months_remaining": round(months_remaining, 1),
            "required_monthly_contribution": round(required_monthly, 2),
            "current_monthly_savings": round(savings_analysis["monthly_savings"], 2),
            "on_track": on_track,
            "milestones": milestones,
            "recommendations": recommendations,
            "savings_analysis": savings_analysis,
        }
    
    @staticmethod
    def get_all_goal_milestones(
        db: Session,
        user_id: str,
        current_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """Get adaptive milestones for all active goals"""
        if current_date is None:
            current_date = datetime.utcnow()
        
        goals = db.query(Goal).filter(
            and_(
                Goal.user_id == user_id,
                Goal.status == GoalStatus.ACTIVE
            )
        ).all()
        
        results = []
        for goal in goals:
            try:
                milestone_data = GoalMilestoneAdjuster.calculate_adaptive_milestones(
                    db, user_id, goal.id, current_date
                )
                results.append(milestone_data)
            except Exception as e:
                logger.error(f"Error calculating milestones for goal {goal.id}: {e}")
                continue
        
        return results
    
    @staticmethod
    def _analyze_savings_rate(
        db: Session,
        user_id: str,
        current_date: datetime,
        lookback_days: int = 90,
    ) -> Dict:
        """
        Analyze recent savings rate (income - expenses)
        
        Args:
            db: Database session
            user_id: User ID
            current_date: Current date
            lookback_days: Days to look back (default 90)
            
        Returns:
            Dict with savings analysis
        """
        lookback_start = current_date - timedelta(days=lookback_days)
        
        # Get income
        total_income = db.query(
            func.sum(Transaction.amount)
        ).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.INCOME,
                Transaction.date >= lookback_start,
                Transaction.date < current_date
            )
        ).scalar() or 0
        
        # Get expenses
        total_expenses = db.query(
            func.sum(Transaction.amount)
        ).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.date >= lookback_start,
                Transaction.date < current_date
            )
        ).scalar() or 0
        
        # Calculate savings
        total_savings = total_income - total_expenses
        
        # Calculate monthly averages
        months = lookback_days / 30
        monthly_income = total_income / months if months > 0 else 0
        monthly_expenses = total_expenses / months if months > 0 else 0
        monthly_savings = total_savings / months if months > 0 else 0
        
        # Calculate savings rate
        savings_rate = (total_savings / total_income * 100) if total_income > 0 else 0
        
        return {
            "lookback_days": lookback_days,
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "total_savings": round(total_savings, 2),
            "monthly_income": round(monthly_income, 2),
            "monthly_expenses": round(monthly_expenses, 2),
            "monthly_savings": round(monthly_savings, 2),
            "savings_rate": round(savings_rate, 2),
        }
    
    @staticmethod
    def _generate_milestones(
        goal: Goal,
        current_date: datetime,
        savings_analysis: Dict,
        on_track: bool,
    ) -> List[Dict]:
        """
        Generate adaptive milestone dates and amounts
        
        If on track: Use original timeline
        If behind: Adjust dates based on current savings rate
        If ahead: Suggest earlier completion
        """
        milestones = []
        
        progress_pct = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
        monthly_savings = savings_analysis["monthly_savings"]
        
        for milestone_pct in GoalMilestoneAdjuster.MILESTONES:
            milestone_amount = goal.target_amount * milestone_pct
            
            # Check if already achieved
            if goal.current_amount >= milestone_amount:
                status = "achieved"
                estimated_date = current_date  # Already done
            else:
                # Calculate when we'll reach this milestone
                remaining_to_milestone = milestone_amount - goal.current_amount
                
                if monthly_savings > 0:
                    months_to_milestone = remaining_to_milestone / monthly_savings
                    estimated_date = current_date + relativedelta(months=int(months_to_milestone))
                else:
                    # No savings, use original timeline
                    time_ratio = (milestone_pct - (progress_pct / 100)) / (1 - (progress_pct / 100))
                    days_to_milestone = (goal.target_date - current_date).days * time_ratio
                    estimated_date = current_date + timedelta(days=int(days_to_milestone))
                
                # Check if on track for this milestone
                original_milestone_date = goal.target_date - timedelta(
                    days=(goal.target_date - current_date).days * (1 - milestone_pct)
                )
                
                if estimated_date <= original_milestone_date:
                    status = "on_track"
                elif estimated_date <= original_milestone_date + timedelta(days=30):
                    status = "at_risk"
                else:
                    status = "behind"
            
            milestones.append({
                "percentage": int(milestone_pct * 100),
                "amount": round(milestone_amount, 2),
                "estimated_date": estimated_date.strftime("%Y-%m-%d"),
                "status": status,
                "is_achieved": status == "achieved",
            })
        
        return milestones
    
    @staticmethod
    def _generate_recommendations(
        goal: Goal,
        savings_analysis: Dict,
        required_monthly: float,
        on_track: bool,
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        monthly_savings = savings_analysis["monthly_savings"]
        shortfall = required_monthly - monthly_savings
        
        if not on_track and shortfall > 0:
            recommendations.append(
                f"You need to save an additional ${shortfall:,.2f}/month to reach your goal on time"
            )
            
            # Suggest specific actions
            if shortfall < monthly_savings * 0.2:
                recommendations.append(
                    "Small adjustment needed: Consider reducing discretionary spending by 10-15%"
                )
            elif shortfall < monthly_savings * 0.5:
                recommendations.append(
                    "Moderate adjustment needed: Review your budget and identify areas to cut back"
                )
            else:
                recommendations.append(
                    "Significant adjustment needed: Consider extending your goal deadline or increasing income"
                )
        
        elif on_track and monthly_savings > required_monthly * 1.2:
            ahead_by = monthly_savings - required_monthly
            recommendations.append(
                f"Great progress! You're saving ${ahead_by:,.2f}/month more than needed"
            )
            recommendations.append(
                "Consider moving up your goal date or increasing your target amount"
            )
        
        else:
            recommendations.append(
                "You're on track! Keep up your current savings rate"
            )
        
        # Savings rate recommendations
        if savings_analysis["savings_rate"] < 10:
            recommendations.append(
                f"Your savings rate is {savings_analysis['savings_rate']:.1f}%. Aim for at least 20% for healthy financial progress"
            )
        elif savings_analysis["savings_rate"] >= 20:
            recommendations.append(
                f"Excellent savings rate of {savings_analysis['savings_rate']:.1f}%! You're building strong financial habits"
            )
        
        return recommendations
