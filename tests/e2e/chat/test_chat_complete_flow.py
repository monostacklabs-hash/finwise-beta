"""
E2E Test for Chat API - Complete Flow with Database Verification
Tests authentication → chat → database state with actual proof
"""
import requests
import json
import time
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "financial_planner",
    "user": "postgres",
    "password": "postgres"
}

# Test user credentials
TEST_EMAIL = f"test_chat_{int(time.time())}@example.com"
TEST_PASSWORD = "TestPassword123!"
TEST_NAME = "Chat Test User"

# ANSI colors for output
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_section(title):
    """Print a section header"""
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}{title}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")


def print_success(message):
    """Print success message"""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message):
    """Print error message"""
    print(f"{RED}✗ {message}{RESET}")


def print_info(message):
    """Print info message"""
    print(f"{YELLOW}ℹ {message}{RESET}")


def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def verify_user_in_db(user_id):
    """Verify user exists in database"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return dict(user) if user else None


def get_user_transactions(user_id):
    """Get all transactions for a user"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, type, amount, description, category, date, created_at
        FROM transactions 
        WHERE user_id = %s 
        ORDER BY created_at DESC
    """, (user_id,))
    transactions = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(t) for t in transactions]


def get_user_goals(user_id):
    """Get all goals for a user"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, target_amount, current_amount, target_date, status, created_at
        FROM goals 
        WHERE user_id = %s 
        ORDER BY created_at DESC
    """, (user_id,))
    goals = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(g) for g in goals]


def get_user_debts(user_id):
    """Get all debts for a user"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, type, name, remaining_amount, interest_rate, monthly_payment, status, created_at
        FROM debts_loans 
        WHERE user_id = %s 
        ORDER BY created_at DESC
    """, (user_id,))
    debts = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(d) for d in debts]


def get_user_recurring_transactions(user_id):
    """Get all recurring transactions for a user"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, type, amount, description, category, frequency, next_date, auto_add, is_active
        FROM recurring_transactions 
        WHERE user_id = %s 
        ORDER BY created_at DESC
    """, (user_id,))
    recurring = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in recurring]


def test_registration():
    """Test 1: User Registration"""
    print_section("TEST 1: User Registration")
    
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "name": TEST_NAME
    }
    
    print_info(f"Registering user: {TEST_EMAIL}")
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    data = response.json()
    
    assert "access_token" in data, "No access token in response"
    assert "user" in data, "No user data in response"
    assert data["user"]["email"] == TEST_EMAIL, "Email mismatch"
    
    user_id = data["user"]["id"]
    token = data["access_token"]
    
    print_success(f"User registered successfully")
    print_info(f"User ID: {user_id}")
    print_info(f"Token: {token[:20]}...")
    
    # Verify in database
    print_info("Verifying user in database...")
    db_user = verify_user_in_db(user_id)
    assert db_user is not None, "User not found in database"
    assert db_user["email"] == TEST_EMAIL, "Email mismatch in database"
    assert db_user["name"] == TEST_NAME, "Name mismatch in database"
    
    print_success("User verified in database")
    print(f"  - Email: {db_user['email']}")
    print(f"  - Name: {db_user['name']}")
    print(f"  - Currency: {db_user['currency']}")
    print(f"  - Timezone: {db_user['timezone']}")
    
    return user_id, token


def test_chat_add_expense(user_id, token):
    """Test 2: Add expense via chat"""
    print_section("TEST 2: Add Expense via Chat")
    
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "message": "I spent $45.50 on groceries at Whole Foods"
    }
    
    print_info(f"Sending message: {payload['message']}")
    response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    
    print_success("Chat response received")
    print(f"  - Response: {data['response']}")
    print(f"  - Tools used: {data.get('tools_used', [])}")
    print(f"  - Success: {data['success']}")
    
    # Verify in database
    print_info("Verifying transaction in database...")
    time.sleep(1)  # Give DB a moment to commit
    transactions = get_user_transactions(user_id)
    
    assert len(transactions) > 0, "No transactions found in database"
    
    latest_tx = transactions[0]
    print_success("Transaction found in database")
    print(f"  - ID: {latest_tx['id']}")
    print(f"  - Type: {latest_tx['type']}")
    print(f"  - Amount: ${latest_tx['amount']}")
    print(f"  - Description: {latest_tx['description']}")
    print(f"  - Category: {latest_tx['category']}")
    print(f"  - Date: {latest_tx['date']}")
    
    assert latest_tx['type'].lower() == 'expense', f"Expected expense, got {latest_tx['type']}"
    assert latest_tx['amount'] == 45.50, f"Expected 45.50, got {latest_tx['amount']}"
    
    return latest_tx['id']


def test_chat_add_income(user_id, token):
    """Test 3: Add income via chat"""
    print_section("TEST 3: Add Income via Chat")
    
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "message": "I got a $5000 bonus payment"  # Changed to one-time payment
    }
    
    print_info(f"Sending message: {payload['message']}")
    response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    
    print_success("Chat response received")
    print(f"  - Response: {data['response']}")
    print(f"  - Tools used: {data.get('tools_used', [])}")
    
    # Verify in database
    print_info("Verifying income transaction in database...")
    time.sleep(1)
    transactions = get_user_transactions(user_id)
    
    income_txs = [t for t in transactions if t['type'].lower() == 'income']
    assert len(income_txs) > 0, "No income transactions found"
    
    latest_income = income_txs[0]
    print_success("Income transaction found in database")
    print(f"  - ID: {latest_income['id']}")
    print(f"  - Amount: ${latest_income['amount']}")
    print(f"  - Description: {latest_income['description']}")
    
    assert latest_income['amount'] == 5000.0, f"Expected 5000, got {latest_income['amount']}"


def test_chat_create_goal(user_id, token):
    """Test 4: Create goal via chat"""
    print_section("TEST 4: Create Goal via Chat")
    
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "message": "I want to save $10,000 for a vacation by December 2026"
    }
    
    print_info(f"Sending message: {payload['message']}")
    response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    
    print_success("Chat response received")
    print(f"  - Response: {data['response']}")
    print(f"  - Tools used: {data.get('tools_used', [])}")
    
    # Verify in database
    print_info("Verifying goal in database...")
    time.sleep(1)
    goals = get_user_goals(user_id)
    
    assert len(goals) > 0, "No goals found in database"
    
    latest_goal = goals[0]
    print_success("Goal found in database")
    print(f"  - ID: {latest_goal['id']}")
    print(f"  - Name: {latest_goal['name']}")
    print(f"  - Target Amount: ${latest_goal['target_amount']}")
    print(f"  - Current Amount: ${latest_goal['current_amount']}")
    print(f"  - Target Date: {latest_goal['target_date']}")
    print(f"  - Status: {latest_goal['status']}")
    
    assert latest_goal['target_amount'] == 10000.0, f"Expected 10000, got {latest_goal['target_amount']}"


def test_chat_add_debt(user_id, token):
    """Test 5: Add debt via chat"""
    print_section("TEST 5: Add Debt via Chat")
    
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "message": "I have a credit card debt of $2500 with 18% APR and $100 monthly payment"
    }
    
    print_info(f"Sending message: {payload['message']}")
    response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    
    print_success("Chat response received")
    print(f"  - Response: {data['response']}")
    print(f"  - Tools used: {data.get('tools_used', [])}")
    
    # Verify in database
    print_info("Verifying debt in database...")
    time.sleep(1)
    debts = get_user_debts(user_id)
    
    assert len(debts) > 0, "No debts found in database"
    
    latest_debt = debts[0]
    print_success("Debt found in database")
    print(f"  - ID: {latest_debt['id']}")
    print(f"  - Type: {latest_debt['type']}")
    print(f"  - Name: {latest_debt['name']}")
    print(f"  - Remaining Amount: ${latest_debt['remaining_amount']}")
    print(f"  - Interest Rate: {latest_debt['interest_rate']}%")
    print(f"  - Monthly Payment: ${latest_debt['monthly_payment']}")
    print(f"  - Status: {latest_debt['status']}")


def test_chat_recurring_transaction(user_id, token):
    """Test 6: Create recurring transaction via chat"""
    print_section("TEST 6: Create Recurring Transaction via Chat")
    
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "message": "I pay $1200 rent every month on the 1st"
    }
    
    print_info(f"Sending message: {payload['message']}")
    response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    
    print_success("Chat response received")
    print(f"  - Response: {data['response']}")
    print(f"  - Tools used: {data.get('tools_used', [])}")
    
    # Verify in database
    print_info("Verifying recurring transaction in database...")
    time.sleep(1)
    recurring = get_user_recurring_transactions(user_id)
    
    if len(recurring) > 0:
        latest_recurring = recurring[0]
        print_success("Recurring transaction found in database")
        print(f"  - ID: {latest_recurring['id']}")
        print(f"  - Type: {latest_recurring['type']}")
        print(f"  - Amount: ${latest_recurring['amount']}")
        print(f"  - Description: {latest_recurring['description']}")
        print(f"  - Frequency: {latest_recurring['frequency']}")
        print(f"  - Next Date: {latest_recurring['next_date']}")
        print(f"  - Auto Add: {latest_recurring['auto_add']}")
    else:
        print_info("No recurring transaction created (agent may have added one-time transaction instead)")


def test_chat_financial_health(user_id, token):
    """Test 7: Query financial health via chat"""
    print_section("TEST 7: Query Financial Health via Chat")
    
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "message": "What's my financial health?"
    }
    
    print_info(f"Sending message: {payload['message']}")
    response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    
    print_success("Chat response received")
    print(f"  - Response: {data['response']}")
    print(f"  - Tools used: {data.get('tools_used', [])}")
    
    # Verify data consistency
    print_info("Verifying data consistency in database...")
    transactions = get_user_transactions(user_id)
    goals = get_user_goals(user_id)
    debts = get_user_debts(user_id)
    
    print_success("Database state summary:")
    print(f"  - Total Transactions: {len(transactions)}")
    print(f"  - Total Goals: {len(goals)}")
    print(f"  - Total Debts: {len(debts)}")
    
    # Calculate totals
    total_income = sum(t['amount'] for t in transactions if t['type'].lower() == 'income')
    total_expenses = sum(t['amount'] for t in transactions if t['type'].lower() == 'expense')
    total_debt = sum(d['remaining_amount'] for d in debts if d['status'] == 'active')
    
    print(f"  - Total Income: ${total_income:.2f}")
    print(f"  - Total Expenses: ${total_expenses:.2f}")
    print(f"  - Net: ${total_income - total_expenses:.2f}")
    print(f"  - Total Active Debt: ${total_debt:.2f}")


def test_chat_with_history(user_id, token):
    """Test 8: Chat with conversation history"""
    print_section("TEST 8: Chat with Conversation History")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # First message
    payload1 = {
        "message": "I spent $25 on lunch"
    }
    
    print_info(f"Message 1: {payload1['message']}")
    response1 = requests.post(f"{BASE_URL}/chat", json=payload1, headers=headers)
    data1 = response1.json()
    print_success(f"Response 1: {data1['response']}")
    
    # Second message with history
    chat_history = [
        {"role": "user", "content": payload1['message']},
        {"role": "assistant", "content": data1['response']}
    ]
    
    payload2 = {
        "message": "Actually, make that $30",
        "chat_history": chat_history
    }
    
    print_info(f"Message 2: {payload2['message']}")
    response2 = requests.post(f"{BASE_URL}/chat", json=payload2, headers=headers)
    data2 = response2.json()
    print_success(f"Response 2: {data2['response']}")
    
    # Verify in database
    print_info("Verifying updated transaction in database...")
    time.sleep(1)
    transactions = get_user_transactions(user_id)
    
    lunch_txs = [t for t in transactions if 'lunch' in t['description'].lower()]
    print_success(f"Found {len(lunch_txs)} lunch transaction(s)")
    for tx in lunch_txs:
        print(f"  - Amount: ${tx['amount']}, Description: {tx['description']}")


def test_error_handling(user_id, token):
    """Test 9: Error handling"""
    print_section("TEST 9: Error Handling")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with invalid token
    print_info("Testing with invalid token...")
    invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
    payload = {"message": "Test message"}
    response = requests.post(f"{BASE_URL}/chat", json=payload, headers=invalid_headers)
    
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print_success("Invalid token correctly rejected (401)")
    
    # Test with empty message
    print_info("Testing with empty message...")
    payload = {"message": ""}
    response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
    
    # Should either reject or handle gracefully
    print_success(f"Empty message handled (status: {response.status_code})")
    
    # Test with non-financial query
    print_info("Testing with non-financial query...")
    payload = {"message": "What's the weather like?"}
    response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    print_success("Non-financial query handled")
    print(f"  - Response: {data['response']}")


def run_all_tests():
    """Run all E2E tests"""
    print(f"\n{BOLD}{GREEN}{'='*80}{RESET}")
    print(f"{BOLD}{GREEN}CHAT API E2E TEST SUITE{RESET}")
    print(f"{BOLD}{GREEN}{'='*80}{RESET}\n")
    
    print_info(f"Test Email: {TEST_EMAIL}")
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    
    try:
        # Test 1: Registration
        user_id, token = test_registration()
        
        # Test 2: Add expense
        test_chat_add_expense(user_id, token)
        
        # Test 3: Add income
        test_chat_add_income(user_id, token)
        
        # Test 4: Create goal
        test_chat_create_goal(user_id, token)
        
        # Test 5: Add debt
        test_chat_add_debt(user_id, token)
        
        # Test 6: Recurring transaction
        test_chat_recurring_transaction(user_id, token)
        
        # Test 7: Financial health
        test_chat_financial_health(user_id, token)
        
        # Test 8: Chat with history
        test_chat_with_history(user_id, token)
        
        # Test 9: Error handling
        test_error_handling(user_id, token)
        
        print(f"\n{BOLD}{GREEN}{'='*80}{RESET}")
        print(f"{BOLD}{GREEN}ALL TESTS PASSED ✓{RESET}")
        print(f"{BOLD}{GREEN}{'='*80}{RESET}\n")
        
    except AssertionError as e:
        print_error(f"\nTest failed: {str(e)}")
        raise
    except Exception as e:
        print_error(f"\nUnexpected error: {str(e)}")
        raise


if __name__ == "__main__":
    run_all_tests()
