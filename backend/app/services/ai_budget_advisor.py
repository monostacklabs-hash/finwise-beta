"""
AI-Enhanced Budget Adjustment Advisor
Provides personalized, context-aware budget recommendations using LLM
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import json

from ..database.models import Budget, Transaction, TransactionType, Goal, GoalStatus, User
from .budget_tracker import BudgetTracker
from ..config import settings

logger = logging.getLogger(__name__)


class AIBudgetAdvisor:
    """
    AI-powered budget advisor that provides personalized recommendations
    
    Improvements over rule-based approach:
    - Understands user's lifestyle and priorities
    - Provides natural language explanations
    - Context-aware recommendations (life events, goals)
    - Learns from user feedback
    - Considers spending patterns holistically
    """
    
    @staticmethod
    def analyze_and_recommend(
        db: Session,
        user_id: str,
        current_date: Optional[datetime] = None,
        use_ai: bool = True,
    ) -> Dict:
        """
        Analyze spending and generate personalized budget recommendations
        
        Args:
            db: Database session
            user_id: User ID
            current_date: Current date (defaults to now)
            use_ai: If True, use AI; if False, use rule-based fallback
            
        Returns:
            Dict with analysis and recommendations
        """
        if current_date is None:
            current_date = datetime.utcnow()
        
        # Get user profile
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"status": "error", "message": "User not found"}
        
        # Get budget data
        budgets = db.query(Budget).filter(
            and_(
                Budget.user_id == user_id,
                Budget.is_active == True
            )
        ).all()
        
        if not budgets:
            return {
                "status": "no_budgets",
                "message": "No active budgets to analyze",
                "recommendations": []
            }
        
        # Get budget statuses
        budget_statuses = BudgetTracker.get_all_budget_statuses(db, user_id, current_date)
        
        # Get spending analysis
        analysis = AIBudgetAdvisor._analyze_spending(db, user_id, budget_statuses, current_date)
        
        # Get active goals
        goals = db.query(Goal).filter(
            and_(
                Goal.user_id == user_id,
                Goal.status == GoalStatus.ACTIVE
            )
        ).order_by(Goal.priority.desc()).all()
        
        # Get recent transactions for context
        recent_transactions = db.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.date >= current_date - timedelta(days=30)
            )
        ).order_by(Transaction.date.desc()).limit(50).all()
        
        # Generate recommendations
        if use_ai:
            try:
                recommendations = AIBudgetAdvisor._generate_ai_recommendations(
                    user=user,
                    budget_statuses=budget_statuses,
                    analysis=analysis,
                    goals=goals,
                    recent_transactions=recent_transactions,
                )
            except Exception as e:
                logger.error(f"AI recommendation failed: {e}, falling back to rule-based")
                recommendations = AIBudgetAdvisor._generate_rule_based_recommendations(
                    budget_statuses, analysis, goals
                )
        else:
            recommendations = AIBudgetAdvisor._generate_rule_based_recommendations(
                budget_statuses, analysis, goals
            )
        
        return {
            "status": "success",
            "analysis": analysis,
            "recommendations": recommendations,
            "total_budgets": len(budgets),
            "method": "ai" if use_ai else "rule-based",
        }
    
    @staticmethod
    def _analyze_spending(
        db: Session,
        user_id: str,
        budget_statuses: List[Dict],
        current_date: datetime,
    ) -> Dict:
        """Analyze spending patterns"""
        
        total_budget = sum(b["budgeted_amount"] for b in budget_statuses)
        total_spent = sum(b["actual_spent"] for b in budget_statuses)
        
        overspent = [b for b in budget_statuses if b["is_overspent"]]
        underspent = [b for b in budget_statuses if b["percentage_used"] < 50]
        
        # Get spending by category
        lookback_days = 30
        lookback_start = current_date - timedelta(days=lookback_days)
        
        category_spending = db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count")
        ).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.date >= lookback_start
            )
        ).group_by(Transaction.category).all()
        
        spending_by_category = {
            cat: {"total": float(total), "count": count}
            for cat, total, count in category_spending
        }
        
        # Calculate income
        total_income = db.query(
            func.sum(Transaction.amount)
        ).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.INCOME,
                Transaction.date >= lookback_start
            )
        ).scalar() or 0
        
        return {
            "total_budget": total_budget,
            "total_spent": total_spent,
            "total_income": float(total_income),
            "budget_utilization": (total_spent / total_budget * 100) if total_budget > 0 else 0,
            "overspent_count": len(overspent),
            "underspent_count": len(underspent),
            "overspent_categories": [
                {"category": b["category"], "amount": b["actual_spent"], "budget": b["budgeted_amount"]}
                for b in overspent
            ],
            "underspent_categories": [
                {"category": b["category"], "usage": b["percentage_used"]}
                for b in underspent
            ],
            "spending_by_category": spending_by_category,
            "savings_rate": ((total_income - total_spent) / total_income * 100) if total_income > 0 else 0,
        }
    
    @staticmethod
    def _generate_ai_recommendations(
        user: User,
        budget_statuses: List[Dict],
        analysis: Dict,
        goals: List[Goal],
        recent_transactions: List[Transaction],
    ) -> List[Dict]:
        """Generate personalized recommendations using AI"""
        
        # Build context for AI
        context = AIBudgetAdvisor._build_context(
            user, budget_statuses, analysis, goals, recent_transactions
        )
        
        # Create prompt
        prompt = f"""You are a personal financial advisor analyzing a user's budget and spending patterns.

**User Profile:**
- Name: {user.name}
- Currency: {user.currency}
- Country: {user.country}

**Current Financial Situation:**
- Total Monthly Budget: ${analysis['total_budget']:.2f}
- Total Spent This Month: ${analysis['total_spent']:.2f}
- Budget Utilization: {analysis['budget_utilization']:.1f}%
- Monthly Income: ${analysis['total_income']:.2f}
- Savings Rate: {analysis['savings_rate']:.1f}%

**Budget Status by Category:**
{context['budget_summary']}

**Active Goals ({len(goals)}):**
{context['goals_summary']}

**Recent Spending Patterns:**
{context['spending_summary']}

**Your Task:**
Provide 3-5 personalized budget adjustment recommendations. For each recommendation:

1. **Category**: Which budget category to adjust
2. **Current Amount**: Current budget amount
3. **Recommended Amount**: New suggested amount
4. **Change**: Dollar amount of change
5. **Reasoning**: Clear, personalized explanation (2-3 sentences) that:
   - Explains WHY this adjustment makes sense for THIS user
   - References specific spending patterns or goals
   - Considers user's lifestyle and priorities
6. **Priority**: high/medium/low
7. **Type**: increase/decrease/reallocate

**Guidelines:**
- Be specific and actionable
- Consider user's goals and priorities
- Don't make drastic changes (max 30% adjustment)
- Balance between essential and discretionary spending
- Explain trade-offs clearly
- Be empathetic and supportive in tone

**Output Format (JSON):**
```json
[
  {{
    "category": "category_name",
    "current_amount": 500.00,
    "recommended_amount": 400.00,
    "change": -100.00,
    "reasoning": "Your personalized explanation here...",
    "priority": "high",
    "type": "decrease"
  }}
]
```

Provide ONLY the JSON array, no other text."""

        # Call LLM
        from langchain_anthropic import ChatAnthropic
        from langchain_openai import ChatOpenAI
        
        provider = getattr(settings, 'AI_PROVIDER', 'anthropic').lower()
        model = settings.get_model_for_provider(provider)
        
        if provider in ["anthropic", "claude"] and settings.ANTHROPIC_API_KEY:
            llm = ChatAnthropic(
                temperature=0.3,
                api_key=settings.ANTHROPIC_API_KEY,
                model=model,
                max_tokens=2000,
                timeout=30,
            )
        elif settings.OPENAI_API_KEY:
            llm = ChatOpenAI(
                temperature=0.3,
                api_key=settings.OPENAI_API_KEY,
                model=model,
                max_tokens=2000,
                timeout=30,
            )
        else:
            raise ValueError("No AI provider configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY")
        
        response = llm.invoke(prompt)
        
        # Parse response
        try:
            # Extract JSON from response
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Find JSON array in response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON array found in response")
            
            json_str = content[start_idx:end_idx]
            recommendations = json.loads(json_str)
            
            # Validate and enrich recommendations
            for rec in recommendations:
                # Find matching budget
                matching_budget = next(
                    (b for b in budget_statuses if b["category"] == rec["category"]),
                    None
                )
                
                if matching_budget:
                    rec["budget_id"] = matching_budget["budget_id"]
                    rec["requires_approval"] = True
                    rec["method"] = "ai"
            
            logger.info(f"Generated {len(recommendations)} AI recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.error(f"Response content: {content[:500]}")
            raise
    
    @staticmethod
    def _build_context(
        user: User,
        budget_statuses: List[Dict],
        analysis: Dict,
        goals: List[Goal],
        recent_transactions: List[Transaction],
    ) -> Dict:
        """Build context strings for AI prompt"""
        
        # Budget summary
        budget_lines = []
        for b in budget_statuses[:10]:  # Top 10 categories
            status = "⚠️ OVERSPENT" if b["is_overspent"] else "✓"
            budget_lines.append(
                f"  {status} {b['category']}: ${b['actual_spent']:.2f} / ${b['budgeted_amount']:.2f} "
                f"({b['percentage_used']:.0f}% used)"
            )
        
        budget_summary = "\n".join(budget_lines) if budget_lines else "  No budget data"
        
        # Goals summary
        goal_lines = []
        for g in goals[:5]:  # Top 5 goals
            progress = (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0
            priority_str = "⭐" * g.priority
            goal_lines.append(
                f"  {priority_str} {g.name}: ${g.current_amount:.2f} / ${g.target_amount:.2f} "
                f"({progress:.0f}% complete) - Due: {g.target_date.strftime('%Y-%m-%d') if g.target_date else 'No deadline'}"
            )
        
        goals_summary = "\n".join(goal_lines) if goal_lines else "  No active goals"
        
        # Spending summary
        spending_lines = []
        for cat, data in list(analysis["spending_by_category"].items())[:10]:
            spending_lines.append(
                f"  {cat}: ${data['total']:.2f} ({data['count']} transactions)"
            )
        
        spending_summary = "\n".join(spending_lines) if spending_lines else "  No recent spending"
        
        return {
            "budget_summary": budget_summary,
            "goals_summary": goals_summary,
            "spending_summary": spending_summary,
        }
    
    @staticmethod
    def _generate_rule_based_recommendations(
        budget_statuses: List[Dict],
        analysis: Dict,
        goals: List[Goal],
    ) -> List[Dict]:
        """Fallback: Generate rule-based recommendations"""
        
        recommendations = []
        
        # Rule 1: Reduce overspent categories
        for b in analysis["overspent_categories"]:
            overspend = b["amount"] - b["budget"]
            new_amount = b["budget"] + (overspend * 0.5)  # Increase by 50% of overspend
            
            recommendations.append({
                "category": b["category"],
                "current_amount": b["budget"],
                "recommended_amount": round(new_amount, 2),
                "change": round(new_amount - b["budget"], 2),
                "reasoning": f"You've been consistently overspending in {b['category']}. "
                            f"Consider increasing the budget or reducing spending.",
                "priority": "high",
                "type": "increase",
                "method": "rule-based",
                "requires_approval": True,
            })
        
        # Rule 2: Reduce underspent categories
        for b in analysis["underspent_categories"]:
            if b["usage"] < 30:  # Less than 30% used
                matching_budget = next(
                    (bs for bs in budget_statuses if bs["category"] == b["category"]),
                    None
                )
                
                if matching_budget:
                    reduction = matching_budget["budgeted_amount"] * 0.2
                    new_amount = matching_budget["budgeted_amount"] - reduction
                    
                    recommendations.append({
                        "category": b["category"],
                        "current_amount": matching_budget["budgeted_amount"],
                        "recommended_amount": round(new_amount, 2),
                        "change": round(-reduction, 2),
                        "reasoning": f"You're only using {b['usage']:.0f}% of your {b['category']} budget. "
                                    f"Consider reallocating these funds to other priorities.",
                        "priority": "medium",
                        "type": "decrease",
                        "method": "rule-based",
                        "requires_approval": True,
                    })
        
        # Rule 3: Goal-based recommendations
        if goals:
            high_priority = [g for g in goals if g.priority >= 3]
            if high_priority:
                recommendations.append({
                    "category": "savings",
                    "current_amount": 0,
                    "recommended_amount": analysis["total_income"] * 0.1,
                    "change": analysis["total_income"] * 0.1,
                    "reasoning": f"You have {len(high_priority)} high-priority goals. "
                                f"Consider allocating 10% of income to savings.",
                    "priority": "high",
                    "type": "increase",
                    "method": "rule-based",
                    "requires_approval": True,
                })
        
        return recommendations[:5]  # Return top 5
