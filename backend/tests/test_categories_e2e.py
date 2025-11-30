"""
E2E Tests for Category System
Tests hierarchical categories and transaction type support
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_get_categories_hierarchy(client: TestClient, auth_headers: dict):
    """Test getting hierarchical category structure"""
    response = client.get("/api/v1/categories", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "categories" in data
    assert "hierarchy" in data
    assert isinstance(data["categories"], list)
    assert len(data["categories"]) > 0


def test_get_category_path(client: TestClient, auth_headers: dict):
    """Test getting full path for a category"""
    response = client.get("/api/v1/categories/fresh_produce/path", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "path" in data
    assert "root" in data
    assert "parent" in data
    assert "children" in data
    assert ">" in data["path"]  # Should have hierarchy separator


def test_get_user_categories(client: TestClient, auth_headers: dict):
    """Test getting user-specific categories with usage counts"""
    response = client.get("/api/v1/user/categories", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "categories" in data
    categories = data["categories"]
    assert len(categories) > 0
    
    # Check category structure
    first_cat = categories[0]
    assert "id" in first_cat
    assert "name" in first_cat
    assert "display_name" in first_cat
    assert "icon" in first_cat
    assert "color" in first_cat


def test_suggest_category_from_description(client: TestClient, auth_headers: dict):
    """Test AI category suggestion from transaction description"""
    response = client.post(
        "/api/v1/categories/suggest",
        headers=auth_headers,
        json={"description": "Bought groceries at Whole Foods"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "category" in data
    assert "confidence" in data
    assert data["category"] in ["groceries", "fresh_produce", "food"]


def test_transaction_with_special_type(client: TestClient, auth_headers: dict):
    """Test creating transaction with special type (upcoming, subscription, etc.)"""
    response = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "type": "expense",
            "special_type": "subscription",
            "amount": 9.99,
            "category": "streaming",
            "description": "Netflix subscription"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["type"] == "expense"
    assert data.get("special_type") == "subscription"
    assert data["category"] == "streaming"


def test_transaction_with_category_hierarchy(client: TestClient, auth_headers: dict):
    """Test transaction with full category path"""
    response = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "type": "expense",
            "amount": 45.50,
            "category": "food > groceries > fresh_produce",
            "description": "Organic vegetables"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should normalize to leaf category
    assert "groceries" in data["category"] or "fresh_produce" in data["category"]


def test_paired_transaction_transfer(client: TestClient, auth_headers: dict):
    """Test creating paired transactions for account transfers"""
    # Create two accounts first
    account1_response = client.post(
        "/api/v1/accounts",
        headers=auth_headers,
        json={
            "account_type": "checking",
            "account_name": "Main Checking",
            "current_balance": 1000.0
        }
    )
    assert account1_response.status_code == 200
    account1 = account1_response.json()
    
    account2_response = client.post(
        "/api/v1/accounts",
        headers=auth_headers,
        json={
            "account_type": "savings",
            "account_name": "Savings Account",
            "current_balance": 5000.0
        }
    )
    assert account2_response.status_code == 200
    account2 = account2_response.json()
    
    # Create transfer (expense from account1, income to account2)
    response = client.post(
        "/api/v1/transactions/transfer",
        headers=auth_headers,
        json={
            "from_account_id": account1["id"],
            "to_account_id": account2["id"],
            "amount": 200.0,
            "description": "Transfer to savings"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "from_transaction" in data
    assert "to_transaction" in data
    assert data["from_transaction"]["paired_transaction_id"] == data["to_transaction"]["id"]
    assert data["to_transaction"]["paired_transaction_id"] == data["from_transaction"]["id"]


def test_upcoming_transaction(client: TestClient, auth_headers: dict):
    """Test creating upcoming transaction (bill reminder)"""
    response = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "type": "expense",
            "special_type": "upcoming",
            "amount": 150.0,
            "category": "utilities",
            "description": "Electric bill",
            "date": "2025-12-01T00:00:00"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["special_type"] == "upcoming"
    assert data["category"] == "utilities"


def test_repetitive_transaction(client: TestClient, auth_headers: dict):
    """Test creating repetitive transaction"""
    response = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "type": "expense",
            "special_type": "repetitive",
            "amount": 50.0,
            "category": "transport > fuel",
            "description": "Weekly gas fill-up"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["special_type"] == "repetitive"


def test_credit_debt_transactions(client: TestClient, auth_headers: dict):
    """Test credit (lent) and debt (borrowed) transactions"""
    # Lent money
    lent_response = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "type": "expense",
            "special_type": "credit",
            "amount": 500.0,
            "category": "uncategorized",
            "description": "Lent to friend"
        }
    )
    
    assert lent_response.status_code == 200
    lent_data = lent_response.json()
    assert lent_data["special_type"] == "credit"
    
    # Borrowed money
    borrowed_response = client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "type": "income",
            "special_type": "debt",
            "amount": 300.0,
            "category": "uncategorized",
            "description": "Borrowed from family"
        }
    )
    
    assert borrowed_response.status_code == 200
    borrowed_data = borrowed_response.json()
    assert borrowed_data["special_type"] == "debt"


def test_category_usage_count_increments(client: TestClient, auth_headers: dict):
    """Test that category usage count increments when used"""
    # Get initial categories
    initial_response = client.get("/api/v1/user/categories", headers=auth_headers)
    initial_categories = {c["name"]: c["usage_count"] for c in initial_response.json()["categories"]}
    
    # Create transaction with groceries category
    client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "type": "expense",
            "amount": 50.0,
            "category": "groceries",
            "description": "Weekly shopping"
        }
    )
    
    # Get updated categories
    updated_response = client.get("/api/v1/user/categories", headers=auth_headers)
    updated_categories = {c["name"]: c["usage_count"] for c in updated_response.json()["categories"]}
    
    # Usage count should have increased
    if "groceries" in initial_categories:
        assert updated_categories["groceries"] > initial_categories["groceries"]
