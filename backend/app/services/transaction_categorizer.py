"""
Transaction Categorization Service (Fallback)
"""
from typing import Dict


class TransactionCategorizer:
    """Rule-based transaction categorization (fallback when AI unavailable)"""

    # Keyword-based categorization rules
    CATEGORY_KEYWORDS = {
        "food": [
            "grocery",
            "restaurant",
            "food",
            "meal",
            "dinner",
            "lunch",
            "breakfast",
            "cafe",
            "coffee",
            "starbucks",
            "mcdonald",
            "pizza",
            "uber eats",
            "doordash",
        ],
        "transport": [
            "uber",
            "lyft",
            "taxi",
            "gas",
            "fuel",
            "parking",
            "metro",
            "bus",
            "train",
            "flight",
            "airline",
        ],
        "utilities": [
            "electric",
            "water",
            "gas bill",
            "internet",
            "phone",
            "mobile",
            "att",
            "verizon",
            "comcast",
        ],
        "entertainment": [
            "movie",
            "netflix",
            "spotify",
            "concert",
            "game",
            "theater",
            "amusement",
        ],
        "shopping": [
            "amazon",
            "walmart",
            "target",
            "mall",
            "clothing",
            "shoes",
            "electronics",
        ],
        "healthcare": [
            "doctor",
            "hospital",
            "pharmacy",
            "medicine",
            "dental",
            "insurance",
            "cvs",
            "walgreens",
        ],
        "education": ["tuition", "book", "course", "school", "university", "training"],
        "salary": ["salary", "paycheck", "wage", "income", "bonus"],
        "investment": ["dividend", "interest", "stock", "investment", "401k"],
    }

    @staticmethod
    def categorize(description: str, amount: float = None, trans_type: str = None) -> Dict:
        """
        Categorize transaction using rule-based approach

        Args:
            description: Transaction description
            amount: Transaction amount (optional)
            trans_type: Transaction type (optional)

        Returns:
            Dictionary with category, type, recurring status, and confidence
        """
        description_lower = description.lower()

        # Find matching category
        category = "uncategorized"
        for cat, keywords in TransactionCategorizer.CATEGORY_KEYWORDS.items():
            if any(keyword in description_lower for keyword in keywords):
                category = cat
                break

        # Determine type if not provided
        if not trans_type:
            if category in ["salary", "investment"]:
                trans_type = "income"
            else:
                trans_type = "expense"

        # Check if recurring (simple heuristic)
        recurring_keywords = [
            "monthly",
            "subscription",
            "recurring",
            "auto",
            "bill",
            "rent",
        ]
        recurring = any(kw in description_lower for kw in recurring_keywords)

        # Confidence based on match
        confidence = 0.8 if category != "uncategorized" else 0.3

        return {
            "category": category,
            "type": trans_type,
            "recurring": recurring,
            "confidence": confidence,
        }
