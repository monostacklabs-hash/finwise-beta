"""
User Category Management Service
Manages personalized category collections for each user
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import json
import logging

from ..database.models import Category, User

logger = logging.getLogger(__name__)


# Default categories to seed for new users
DEFAULT_CATEGORIES = [
    # Food & Dining
    {"name": "groceries", "display_name": "Groceries", "parent": "food", "icon": "shopping-cart", "color": "#4CAF50"},
    {"name": "restaurant", "display_name": "Restaurants", "parent": "food", "icon": "utensils", "color": "#FF9800"},
    {"name": "fast_food", "display_name": "Fast Food", "parent": "food", "icon": "burger", "color": "#FFC107"},
    {"name": "coffee_shops", "display_name": "Coffee Shops", "parent": "food", "icon": "coffee", "color": "#795548"},
    {"name": "food", "display_name": "Food & Dining", "parent": None, "icon": "utensils", "color": "#FF5722"},
    
    # Transportation
    {"name": "gas", "display_name": "Gas & Fuel", "parent": "transport", "icon": "gas-pump", "color": "#2196F3"},
    {"name": "ride_share", "display_name": "Ride Share", "parent": "transport", "icon": "car", "color": "#00BCD4"},
    {"name": "public_transport", "display_name": "Public Transit", "parent": "transport", "icon": "bus", "color": "#009688"},
    {"name": "parking", "display_name": "Parking", "parent": "transport", "icon": "parking", "color": "#607D8B"},
    {"name": "transport", "display_name": "Transportation", "parent": None, "icon": "car", "color": "#3F51B5"},
    
    # Entertainment
    {"name": "streaming", "display_name": "Streaming Services", "parent": "entertainment", "icon": "film", "color": "#E91E63"},
    {"name": "movies", "display_name": "Movies & Theater", "parent": "entertainment", "icon": "ticket", "color": "#9C27B0"},
    {"name": "music", "display_name": "Music", "parent": "entertainment", "icon": "music", "color": "#673AB7"},
    {"name": "games", "display_name": "Gaming", "parent": "entertainment", "icon": "gamepad", "color": "#3F51B5"},
    {"name": "entertainment", "display_name": "Entertainment", "parent": None, "icon": "film", "color": "#9C27B0"},
    
    # Shopping
    {"name": "clothing", "display_name": "Clothing", "parent": "shopping", "icon": "tshirt", "color": "#E91E63"},
    {"name": "electronics", "display_name": "Electronics", "parent": "shopping", "icon": "laptop", "color": "#2196F3"},
    {"name": "home_goods", "display_name": "Home & Garden", "parent": "shopping", "icon": "home", "color": "#4CAF50"},
    {"name": "shopping", "display_name": "Shopping", "parent": None, "icon": "shopping-bag", "color": "#FF9800"},
    
    # Healthcare
    {"name": "pharmacy", "display_name": "Pharmacy", "parent": "health", "icon": "pills", "color": "#F44336"},
    {"name": "doctor", "display_name": "Doctor Visits", "parent": "health", "icon": "stethoscope", "color": "#E91E63"},
    {"name": "dental", "display_name": "Dental", "parent": "health", "icon": "tooth", "color": "#00BCD4"},
    {"name": "health", "display_name": "Healthcare", "parent": None, "icon": "heart", "color": "#F44336"},
    
    # Home
    {"name": "rent", "display_name": "Rent", "parent": "housing", "icon": "home", "color": "#795548"},
    {"name": "utilities", "display_name": "Utilities", "parent": "housing", "icon": "bolt", "color": "#FFC107"},
    {"name": "internet", "display_name": "Internet", "parent": "housing", "icon": "wifi", "color": "#2196F3"},
    {"name": "phone", "display_name": "Phone", "parent": "housing", "icon": "phone", "color": "#009688"},
    {"name": "housing", "display_name": "Housing", "parent": None, "icon": "home", "color": "#795548"},
    
    # Fitness
    {"name": "gym", "display_name": "Gym & Fitness", "parent": "fitness", "icon": "dumbbell", "color": "#FF5722"},
    {"name": "sports", "display_name": "Sports", "parent": "fitness", "icon": "basketball", "color": "#FF9800"},
    {"name": "fitness", "display_name": "Fitness & Sports", "parent": None, "icon": "dumbbell", "color": "#FF5722"},
    
    # Education
    {"name": "tuition", "display_name": "Tuition", "parent": "education", "icon": "graduation-cap", "color": "#3F51B5"},
    {"name": "books", "display_name": "Books & Supplies", "parent": "education", "icon": "book", "color": "#2196F3"},
    {"name": "courses", "display_name": "Online Courses", "parent": "education", "icon": "laptop", "color": "#00BCD4"},
    {"name": "education", "display_name": "Education", "parent": None, "icon": "graduation-cap", "color": "#3F51B5"},
    
    # Insurance
    {"name": "health_insurance", "display_name": "Health Insurance", "parent": "insurance", "icon": "shield", "color": "#F44336"},
    {"name": "auto_insurance", "display_name": "Auto Insurance", "parent": "insurance", "icon": "car", "color": "#2196F3"},
    {"name": "life_insurance", "display_name": "Life Insurance", "parent": "insurance", "icon": "heart", "color": "#E91E63"},
    {"name": "insurance", "display_name": "Insurance", "parent": None, "icon": "shield", "color": "#607D8B"},
    
    # Income
    {"name": "salary", "display_name": "Salary", "parent": "income", "icon": "dollar-sign", "color": "#4CAF50"},
    {"name": "freelance", "display_name": "Freelance", "parent": "income", "icon": "briefcase", "color": "#00BCD4"},
    {"name": "investment", "display_name": "Investment Income", "parent": "income", "icon": "chart-line", "color": "#009688"},
    {"name": "income", "display_name": "Income", "parent": None, "icon": "dollar-sign", "color": "#4CAF50"},
    
    # Other
    {"name": "gifts", "display_name": "Gifts", "parent": None, "icon": "gift", "color": "#E91E63"},
    {"name": "charity", "display_name": "Charity", "parent": None, "icon": "hand-holding-heart", "color": "#9C27B0"},
    {"name": "personal_care", "display_name": "Personal Care", "parent": None, "icon": "spa", "color": "#FF9800"},
    {"name": "pets", "display_name": "Pets", "parent": None, "icon": "paw", "color": "#795548"},
    {"name": "travel", "display_name": "Travel", "parent": None, "icon": "plane", "color": "#00BCD4"},
    {"name": "subscriptions", "display_name": "Subscriptions", "parent": None, "icon": "repeat", "color": "#9C27B0"},
    {"name": "uncategorized", "display_name": "Uncategorized", "parent": None, "icon": "question", "color": "#9E9E9E"},
]


class CategoryManager:
    """Manages user-specific category collections"""
    
    @staticmethod
    def seed_default_categories(user_id: str, db: Session) -> int:
        """
        Seed default categories for a new user
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            Number of categories created
        """
        try:
            # Check if user already has categories
            existing_count = db.query(Category).filter(Category.user_id == user_id).count()
            if existing_count > 0:
                logger.info(f"User {user_id} already has {existing_count} categories, skipping seed")
                return 0
            
            # Create default categories
            categories_created = 0
            for cat_data in DEFAULT_CATEGORIES:
                category = Category(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    name=cat_data["name"],
                    display_name=cat_data["display_name"],
                    parent_category=cat_data.get("parent"),
                    icon=cat_data.get("icon"),
                    color=cat_data.get("color"),
                    is_default=True,
                    is_active=True,
                    usage_count=0,
                    ai_suggested=False,
                )
                db.add(category)
                categories_created += 1
            
            db.commit()
            logger.info(f"Seeded {categories_created} default categories for user {user_id}")
            return categories_created
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error seeding categories for user {user_id}: {e}")
            raise
    
    @staticmethod
    def get_user_categories(user_id: str, db: Session, active_only: bool = True) -> List[Dict]:
        """
        Get all categories for a user
        
        Args:
            user_id: User ID
            db: Database session
            active_only: Only return active categories
            
        Returns:
            List of category dictionaries
        """
        query = db.query(Category).filter(Category.user_id == user_id)
        
        if active_only:
            query = query.filter(Category.is_active == True)
        
        categories = query.order_by(Category.usage_count.desc(), Category.name).all()
        
        return [
            {
                "id": cat.id,
                "name": cat.name,
                "display_name": cat.display_name,
                "parent_category": cat.parent_category,
                "icon": cat.icon,
                "color": cat.color,
                "usage_count": cat.usage_count,
                "ai_suggested": cat.ai_suggested,
                "is_default": cat.is_default,
            }
            for cat in categories
        ]
    
    @staticmethod
    def get_category_names(user_id: str, db: Session, active_only: bool = True) -> List[str]:
        """
        Get list of category names for a user (for AI prompts)
        
        Args:
            user_id: User ID
            db: Database session
            active_only: Only return active categories
            
        Returns:
            List of category names
        """
        query = db.query(Category.name).filter(Category.user_id == user_id)
        
        if active_only:
            query = query.filter(Category.is_active == True)
        
        return [name for (name,) in query.all()]
    
    @staticmethod
    def add_category(
        user_id: str,
        name: str,
        display_name: str,
        db: Session,
        parent_category: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        ai_suggested: bool = False,
    ) -> Optional[Dict]:
        """
        Add a new category for a user
        
        Args:
            user_id: User ID
            name: Category name (lowercase, snake_case)
            display_name: Human-readable name
            db: Database session
            parent_category: Parent category name
            icon: Icon identifier
            color: Color hex code
            ai_suggested: Whether this was suggested by AI
            
        Returns:
            Category dictionary or None if already exists
        """
        try:
            # Check if category already exists
            existing = db.query(Category).filter(
                Category.user_id == user_id,
                Category.name == name
            ).first()
            
            if existing:
                logger.info(f"Category '{name}' already exists for user {user_id}")
                return None
            
            # Create new category
            category = Category(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=name,
                display_name=display_name,
                parent_category=parent_category,
                icon=icon,
                color=color,
                is_default=False,
                is_active=True,
                usage_count=0,
                ai_suggested=ai_suggested,
            )
            
            db.add(category)
            db.commit()
            db.refresh(category)
            
            logger.info(f"Created new category '{name}' for user {user_id} (AI suggested: {ai_suggested})")
            
            return {
                "id": category.id,
                "name": category.name,
                "display_name": category.display_name,
                "parent_category": category.parent_category,
                "icon": category.icon,
                "color": category.color,
                "ai_suggested": category.ai_suggested,
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding category '{name}' for user {user_id}: {e}")
            raise
    
    @staticmethod
    def increment_usage(user_id: str, category_name: str, db: Session) -> None:
        """
        Increment usage count for a category
        
        Args:
            user_id: User ID
            category_name: Category name
            db: Database session
        """
        try:
            category = db.query(Category).filter(
                Category.user_id == user_id,
                Category.name == category_name
            ).first()
            
            if category:
                category.usage_count += 1
                db.commit()
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error incrementing usage for category '{category_name}': {e}")
    
    @staticmethod
    def find_similar_category(
        user_id: str,
        description: str,
        db: Session
    ) -> Optional[str]:
        """
        Find a similar category based on keywords
        
        Args:
            user_id: User ID
            description: Transaction description
            db: Database session
            
        Returns:
            Category name if found, None otherwise
        """
        # Get all user categories with keywords
        categories = db.query(Category).filter(
            Category.user_id == user_id,
            Category.is_active == True,
            Category.keywords.isnot(None)
        ).all()
        
        description_lower = description.lower()
        
        for category in categories:
            try:
                keywords = json.loads(category.keywords) if category.keywords else []
                for keyword in keywords:
                    if keyword.lower() in description_lower:
                        return category.name
            except json.JSONDecodeError:
                continue
        
        return None
