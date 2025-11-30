"""
Category Hierarchy System
Defines hierarchical category structure for budgeting and tracking
"""
from typing import Dict, List, Optional, Set
from dataclasses import dataclass


@dataclass
class CategoryNode:
    """Represents a category in the hierarchy"""
    name: str
    parent: Optional[str] = None
    children: List[str] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class CategoryHierarchy:
    """
    Manages hierarchical category structure
    
    Example:
        Home
        ├── Groceries
        │   ├── Fresh Produce
        │   ├── Packaged Foods
        │   └── Beverages
        ├── Utilities
        │   ├── Electricity
        │   ├── Water
        │   └── Internet
        └── Maintenance
    """
    
    # Default category hierarchy (can be customized per user)
    DEFAULT_HIERARCHY = {
        "home": {
            "children": ["groceries", "utilities", "maintenance", "rent_mortgage"],
            "groceries": ["fresh_produce", "packaged_foods", "beverages", "household_items"],
            "utilities": ["electricity", "water", "gas", "internet", "phone"],
            "maintenance": ["repairs", "cleaning", "lawn_care"],
        },
        "transport": {
            "children": ["fuel", "public_transit", "ride_share", "parking", "vehicle_maintenance"],
        },
        "food": {
            "children": ["dining_out", "fast_food", "coffee_shops", "delivery"],
        },
        "entertainment": {
            "children": ["streaming", "movies", "concerts", "hobbies", "sports"],
            "streaming": ["video", "music", "gaming"],
        },
        "shopping": {
            "children": ["clothing", "electronics", "home_goods", "personal_care"],
        },
        "healthcare": {
            "children": ["medical", "dental", "pharmacy", "insurance", "fitness"],
        },
        "education": {
            "children": ["tuition", "books", "courses", "supplies"],
        },
        "income": {
            "children": ["salary", "freelance", "investments", "side_hustle", "gifts"],
        },
        "savings": {
            "children": ["emergency_fund", "retirement", "investments", "goals"],
        },
    }
    
    def __init__(self, custom_hierarchy: Optional[Dict] = None):
        """
        Initialize category hierarchy
        
        Args:
            custom_hierarchy: Optional custom hierarchy (defaults to DEFAULT_HIERARCHY)
        """
        self.hierarchy = custom_hierarchy or self.DEFAULT_HIERARCHY
        self._build_lookup()
    
    def _build_lookup(self):
        """Build parent-child lookup maps"""
        self.parent_map = {}  # child -> parent
        self.children_map = {}  # parent -> [children]
        
        for parent, config in self.hierarchy.items():
            if "children" in config:
                self.children_map[parent] = config["children"]
                for child in config["children"]:
                    self.parent_map[child] = parent
                    
                    # Check for nested children
                    if child in config:
                        self.children_map[child] = config[child]
                        for grandchild in config[child]:
                            self.parent_map[grandchild] = child
    
    def get_parent(self, category: str) -> Optional[str]:
        """Get parent category"""
        return self.parent_map.get(category.lower())
    
    def get_children(self, category: str) -> List[str]:
        """Get direct children of a category"""
        return self.children_map.get(category.lower(), [])
    
    def get_all_descendants(self, category: str) -> Set[str]:
        """Get all descendants (children, grandchildren, etc.)"""
        descendants = set()
        children = self.get_children(category)
        
        for child in children:
            descendants.add(child)
            descendants.update(self.get_all_descendants(child))
        
        return descendants
    
    def get_ancestors(self, category: str) -> List[str]:
        """Get all ancestors (parent, grandparent, etc.) from bottom to top"""
        ancestors = []
        current = category.lower()
        
        while current in self.parent_map:
            parent = self.parent_map[current]
            ancestors.append(parent)
            current = parent
        
        return ancestors
    
    def get_root_category(self, category: str) -> str:
        """Get the root (top-level) category"""
        ancestors = self.get_ancestors(category)
        return ancestors[-1] if ancestors else category.lower()
    
    def get_full_path(self, category: str) -> str:
        """Get full category path (e.g., 'home > groceries > fresh_produce')"""
        ancestors = self.get_ancestors(category)
        ancestors.reverse()
        ancestors.append(category.lower())
        return " > ".join(ancestors)
    
    def is_descendant_of(self, category: str, potential_ancestor: str) -> bool:
        """Check if category is a descendant of potential_ancestor"""
        ancestors = self.get_ancestors(category)
        return potential_ancestor.lower() in ancestors
    
    def normalize_category(self, category: str) -> str:
        """
        Normalize category name (handle variations)
        
        Examples:
            'Fresh Produce' -> 'fresh_produce'
            'fresh produce' -> 'fresh_produce'
            'FreshProduce' -> 'fresh_produce'
        """
        return category.lower().replace(" ", "_").replace("-", "_")
    
    def get_all_categories(self) -> List[str]:
        """Get all categories (flat list)"""
        categories = set(self.hierarchy.keys())
        categories.update(self.parent_map.keys())
        return sorted(list(categories))
    
    def suggest_category(self, description: str) -> str:
        """
        Suggest category based on description keywords
        
        Args:
            description: Transaction description
            
        Returns:
            Suggested category name
        """
        desc_lower = description.lower()
        
        # Keyword mapping (expanded from transaction_categorizer)
        keyword_map = {
            "fresh_produce": ["produce", "fruit", "vegetable", "organic"],
            "groceries": ["grocery", "supermarket", "whole foods", "trader joe"],
            "dining_out": ["restaurant", "dinner", "lunch", "breakfast", "cafe"],
            "coffee_shops": ["coffee", "starbucks", "cafe", "espresso"],
            "delivery": ["uber eats", "doordash", "grubhub", "delivery"],
            "fuel": ["gas", "fuel", "shell", "chevron", "exxon"],
            "ride_share": ["uber", "lyft", "taxi"],
            "public_transit": ["metro", "bus", "train", "subway", "bart"],
            "streaming": ["netflix", "spotify", "hulu", "disney", "prime video"],
            "electricity": ["electric", "power", "pge", "utility"],
            "internet": ["internet", "comcast", "att", "verizon", "wifi"],
            "phone": ["phone", "mobile", "cell", "t-mobile", "sprint"],
            "medical": ["doctor", "hospital", "clinic", "medical"],
            "pharmacy": ["pharmacy", "cvs", "walgreens", "medicine", "prescription"],
            "salary": ["salary", "paycheck", "wage", "payroll"],
            "freelance": ["freelance", "contract", "consulting", "gig"],
        }
        
        # Check for keyword matches
        for category, keywords in keyword_map.items():
            if any(kw in desc_lower for kw in keywords):
                return category
        
        # Fallback to root categories
        root_keywords = {
            "home": ["home", "house", "rent", "mortgage"],
            "transport": ["transport", "car", "vehicle", "travel"],
            "food": ["food", "meal", "eat"],
            "entertainment": ["entertainment", "fun", "movie", "game"],
            "shopping": ["shop", "store", "amazon", "walmart", "target"],
            "healthcare": ["health", "dental", "insurance"],
            "education": ["education", "school", "course", "book"],
        }
        
        for category, keywords in root_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                return category
        
        return "uncategorized"


# Global instance
CATEGORY_HIERARCHY = CategoryHierarchy()
