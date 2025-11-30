"""
AI-Enhanced Transaction Categorization Service
Uses LLM for semantic understanding with fallback to rule-based
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import json

from ..database.models import Transaction, User, Category
from ..database.category_hierarchy import CATEGORY_HIERARCHY
from .transaction_categorizer import TransactionCategorizer
from .category_manager import CategoryManager
from ..config import settings

logger = logging.getLogger(__name__)


class AITransactionCategorizer:
    """
    AI-powered transaction categorization with learning capabilities
    
    Features:
    - Semantic understanding using LLM
    - Learns from user corrections
    - Context-aware (amount, merchant, time)
    - Hierarchical category support
    - Fallback to rule-based when AI unavailable
    """
    
    @staticmethod
    def categorize(
        description: str,
        amount: float,
        trans_type: str,
        user_id: str,
        db: Session,
        use_ai: bool = True,
    ) -> Dict:
        """
        Categorize transaction using AI with fallback
        
        Args:
            description: Transaction description
            amount: Transaction amount
            trans_type: Transaction type (income/expense)
            user_id: User ID for personalization
            db: Database session for learning from history
            use_ai: Whether to use AI (False for testing/fallback)
            
        Returns:
            Dict with category, confidence, reasoning, and metadata
        """
        # Try AI categorization first
        if use_ai and settings.AI_PROVIDER:
            try:
                result = AITransactionCategorizer._categorize_with_ai(
                    description, amount, trans_type, user_id, db
                )
                if result and result.get("confidence", 0) > 0.5:
                    logger.info(f"AI categorization: {description} -> {result['category']} ({result['confidence']:.2f})")
                    return result
            except Exception as e:
                logger.warning(f"AI categorization failed, falling back to rules: {e}")
        
        # Fallback to rule-based
        logger.info(f"Using rule-based categorization for: {description}")
        result = TransactionCategorizer.categorize(description, amount, trans_type)
        result["method"] = "rule-based"
        result["reasoning"] = "Keyword matching"
        return result
    
    @staticmethod
    def _categorize_with_ai(
        description: str,
        amount: float,
        trans_type: str,
        user_id: str,
        db: Session,
    ) -> Dict:
        """
        Use LLM to categorize transaction with context
        
        This method:
        1. Gets user's historical categorization patterns
        2. Builds context-aware prompt
        3. Calls LLM for categorization
        4. Parses and validates response
        """
        # Get user's recent categorization history for learning
        user_history = AITransactionCategorizer._get_user_history(db, user_id, limit=20)
        
        # Get user's personalized categories
        user_categories = CategoryManager.get_user_categories(user_id, db, active_only=True)
        all_categories = [cat["name"] for cat in user_categories]
        
        # Fallback to default categories if user has none
        if not all_categories:
            all_categories = CATEGORY_HIERARCHY.get_all_categories()
        
        # Build AI prompt
        prompt = AITransactionCategorizer._build_categorization_prompt(
            description, amount, trans_type, user_history, user_categories
        )
        
        # Call LLM
        from langchain_anthropic import ChatAnthropic
        from langchain_openai import ChatOpenAI
        
        # Initialize LLM based on provider
        provider = getattr(settings, 'AI_PROVIDER', 'anthropic').lower()
        model = settings.get_model_for_provider(provider)
        
        if provider in ["anthropic", "claude"] and settings.ANTHROPIC_API_KEY:
            llm = ChatAnthropic(
                api_key=settings.ANTHROPIC_API_KEY,
                model=model,
                temperature=0.3,  # Lower temperature for more consistent categorization
                max_tokens=500,
            )
        elif settings.OPENAI_API_KEY:
            llm = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model=model,
                temperature=0.3,
                max_tokens=500,
            )
        else:
            raise ValueError("No LLM API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY")
        
        # Get response
        response = llm.invoke(prompt)
        response_text = response.content
        
        # Parse response
        result = AITransactionCategorizer._parse_ai_response(response_text, all_categories)
        result["method"] = "ai"
        
        # If AI suggested a new category, add it to user's collection
        if result.get("new_category_suggested"):
            new_cat = result.get("new_category")
            if new_cat:
                CategoryManager.add_category(
                    user_id=user_id,
                    name=new_cat["name"],
                    display_name=new_cat.get("display_name", new_cat["name"].replace("_", " ").title()),
                    db=db,
                    parent_category=new_cat.get("parent"),
                    ai_suggested=True,
                )
                logger.info(f"AI suggested and added new category: {new_cat['name']}")
        
        # Increment usage count for the selected category
        if result.get("category"):
            CategoryManager.increment_usage(user_id, result["category"], db)
        
        return result
    
    @staticmethod
    def _get_user_history(db: Session, user_id: str, limit: int = 20) -> List[Dict]:
        """
        Get user's recent transaction categorization history
        
        This helps the AI learn user's preferences:
        - How they categorize similar transactions
        - Their category usage patterns
        - Merchant-specific preferences
        """
        recent_transactions = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.date.desc())
            .limit(limit)
            .all()
        )
        
        history = []
        for t in recent_transactions:
            if t.category and t.category != "uncategorized":
                history.append({
                    "description": t.description,
                    "amount": t.amount,
                    "category": t.category,
                    "type": t.type.value,
                })
        
        return history
    
    @staticmethod
    def _build_categorization_prompt(
        description: str,
        amount: float,
        trans_type: str,
        user_history: List[Dict],
        user_categories: List[Dict],
    ) -> str:
        """
        Build context-aware prompt for LLM categorization
        
        Includes:
        - Transaction details
        - Available categories
        - User's historical patterns
        - Instructions for response format
        """
        # Format user history
        history_text = ""
        if user_history:
            history_text = "\n**User's Recent Categorization Patterns:**\n"
            for h in user_history[:10]:  # Show top 10
                history_text += f"- '{h['description']}' (${h['amount']:.2f}) → {h['category']}\n"
        
        # Format user's categories (show most used first)
        categories_text = "\n**User's Categories (sorted by usage):**\n"
        
        # Group by parent
        root_cats = [c for c in user_categories if not c.get("parent_category")]
        child_cats = [c for c in user_categories if c.get("parent_category")]
        
        # Show root categories with their children
        for root in root_cats[:15]:  # Top 15 root categories
            categories_text += f"- {root['name']} ({root['display_name']})"
            if root['usage_count'] > 0:
                categories_text += f" [used {root['usage_count']}x]"
            
            # Show children
            children = [c for c in child_cats if c.get("parent_category") == root["name"]]
            if children:
                child_names = [f"{c['name']}" for c in children[:5]]  # Top 5 children
                categories_text += f"\n  → {', '.join(child_names)}"
            categories_text += "\n"
        
        prompt = f"""You are a financial transaction categorization expert. Categorize the following transaction into the most appropriate category.

**Transaction Details:**
- Description: "{description}"
- Amount: ${amount:.2f}
- Type: {trans_type}

{categories_text}

{history_text}

**Instructions:**
1. Choose the MOST SPECIFIC category from the user's existing categories
2. Consider the user's historical patterns and usage frequency
3. Use semantic understanding, not just keywords
4. If NO existing category fits well, you can suggest a NEW category
5. Provide confidence score (0.0 to 1.0)
6. Explain your reasoning briefly

**Response Format (JSON):**
{{
    "category": "category_name",
    "confidence": 0.95,
    "reasoning": "Brief explanation",
    "new_category_suggested": false
}}

**If suggesting a NEW category:**
{{
    "category": "new_category_name",
    "confidence": 0.85,
    "reasoning": "Why existing categories don't fit",
    "new_category_suggested": true,
    "new_category": {{
        "name": "new_category_name",
        "display_name": "New Category Name",
        "parent": "parent_category_if_applicable"
    }}
}}

**Examples:**
- "Whole Foods Market" → "groceries" (not just "food")
- "Netflix subscription" → "streaming" (not just "entertainment")
- "Apple Store" → Could be "electronics" or "groceries" depending on context

Respond ONLY with valid JSON, no other text."""

        return prompt
    
    @staticmethod
    def _parse_ai_response(response_text: str, valid_categories: List[str]) -> Dict:
        """
        Parse and validate AI response
        
        Handles:
        - JSON parsing
        - Category validation
        - New category suggestions
        - Confidence normalization
        - Error recovery
        """
        try:
            # Try to extract JSON from response
            # Sometimes LLM adds markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            # Validate and normalize
            category = result.get("category", "uncategorized").lower().replace(" ", "_")
            confidence = float(result.get("confidence", 0.7))
            reasoning = result.get("reasoning", "AI categorization")
            new_category_suggested = result.get("new_category_suggested", False)
            new_category = result.get("new_category")
            
            # If new category suggested, validate it
            if new_category_suggested and new_category:
                # Normalize new category name
                new_category["name"] = new_category.get("name", category).lower().replace(" ", "_")
                
                return {
                    "category": new_category["name"],
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "new_category_suggested": True,
                    "new_category": new_category,
                }
            
            # Validate category exists in user's categories
            if category not in valid_categories:
                # Try to find closest match or use root category
                root = CATEGORY_HIERARCHY.get_root_category(category)
                if root in valid_categories:
                    category = root
                    confidence *= 0.8  # Reduce confidence for fallback
                else:
                    category = "uncategorized"
                    confidence = 0.5
            
            # Normalize confidence to 0-1 range
            confidence = max(0.0, min(1.0, confidence))
            
            return {
                "category": category,
                "confidence": confidence,
                "reasoning": reasoning,
                "new_category_suggested": False,
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {response_text[:200]}")
            return {
                "category": "uncategorized",
                "confidence": 0.3,
                "reasoning": "Failed to parse AI response",
                "new_category_suggested": False,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return {
                "category": "uncategorized",
                "confidence": 0.3,
                "reasoning": "Error in AI categorization",
                "new_category_suggested": False,
                "error": str(e),
            }
    
    @staticmethod
    def learn_from_correction(
        db: Session,
        transaction_id: str,
        old_category: str,
        new_category: str,
        user_id: str,
    ) -> bool:
        """
        Learn from user correction
        
        Future enhancement: Store corrections in a feedback table
        to improve AI categorization over time
        
        Args:
            db: Database session
            transaction_id: Transaction ID
            old_category: AI-suggested category
            new_category: User-corrected category
            user_id: User ID
            
        Returns:
            Success status
        """
        try:
            # Update transaction
            transaction = db.query(Transaction).filter(
                Transaction.id == transaction_id,
                Transaction.user_id == user_id
            ).first()
            
            if transaction:
                transaction.category = new_category
                db.commit()
                
                logger.info(
                    f"Learned from correction: '{transaction.description}' "
                    f"{old_category} → {new_category}"
                )
                
                # TODO: Store in feedback table for future training
                # This would enable:
                # - Pattern recognition for similar transactions
                # - User-specific category preferences
                # - Continuous improvement of AI model
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error learning from correction: {e}")
            db.rollback()
            return False

