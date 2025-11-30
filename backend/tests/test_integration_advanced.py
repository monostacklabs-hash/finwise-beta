"""
Integration test for advanced features through API and agent
"""
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.category_hierarchy import CATEGORY_HIERARCHY


def test_category_hierarchy_integration():
    """Test category hierarchy works correctly"""
    # Test basic operations
    assert CATEGORY_HIERARCHY.get_parent("groceries") == "home"
    assert CATEGORY_HIERARCHY.get_root_category("fresh_produce") == "home"
    
    # Test path generation
    path = CATEGORY_HIERARCHY.get_full_path("fresh_produce")
    assert "home" in path
    assert "groceries" in path
    
    # Test category suggestion
    category = CATEGORY_HIERARCHY.suggest_category("Whole Foods groceries")
    assert category in ["groceries", "fresh_produce", "home"]
    
    # Test all categories are accessible
    all_cats = CATEGORY_HIERARCHY.get_all_categories()
    assert len(all_cats) > 20  # Should have many categories
    assert "home" in all_cats
    assert "groceries" in all_cats
    assert "transport" in all_cats


def test_category_normalization():
    """Test category name normalization"""
    assert CATEGORY_HIERARCHY.normalize_category("Fresh Produce") == "fresh_produce"
    assert CATEGORY_HIERARCHY.normalize_category("fresh produce") == "fresh_produce"
    assert CATEGORY_HIERARCHY.normalize_category("FreshProduce") == "freshproduce"


def test_category_descendants():
    """Test getting all descendants"""
    descendants = CATEGORY_HIERARCHY.get_all_descendants("home")
    assert "groceries" in descendants
    assert "utilities" in descendants
    
    # Check nested descendants
    if "groceries" in CATEGORY_HIERARCHY.children_map:
        grocery_children = CATEGORY_HIERARCHY.get_children("groceries")
        for child in grocery_children:
            assert child in descendants


def test_category_ancestors():
    """Test getting ancestors"""
    ancestors = CATEGORY_HIERARCHY.get_ancestors("fresh_produce")
    assert "groceries" in ancestors
    assert "home" in ancestors


def test_category_suggestions():
    """Test category suggestions for common transactions"""
    test_cases = [
        ("Whole Foods", ["groceries", "fresh_produce", "home"]),
        ("Uber ride", ["ride_share", "transport"]),
        ("Netflix subscription", ["streaming", "entertainment"]),
        ("Starbucks coffee", ["coffee_shops", "food"]),
        ("Shell gas station", ["fuel", "transport"]),
        ("Electric bill", ["electricity", "utilities", "home"]),
    ]
    
    for description, expected_categories in test_cases:
        suggested = CATEGORY_HIERARCHY.suggest_category(description)
        # Should match at least one expected category
        assert any(cat in suggested or suggested in cat for cat in expected_categories), \
            f"Expected {description} to suggest one of {expected_categories}, got {suggested}"


if __name__ == "__main__":
    # Run basic tests
    test_category_hierarchy_integration()
    test_category_normalization()
    test_category_descendants()
    test_category_ancestors()
    test_category_suggestions()
    print("✅ All integration tests passed!")
