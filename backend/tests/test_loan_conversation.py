"""
E2E Test: Loan Agent Conversational Flow
Tests that agent asks for missing loan details instead of making assumptions
"""
import asyncio
from backend.app.agents.financial_agent import get_financial_agent
from backend.app.database.session import get_db
from backend.app.database.models import DebtLoan
import uuid


async def test_loan_conversation_flow():
    """Test multi-turn conversation for loan creation"""
    
    # Setup
    db = next(get_db())
    user_id = str(uuid.uuid4())
    agent = get_financial_agent()
    
    user_data = {
        "timezone": "Asia/Kolkata",
        "currency": "INR",
        "country": "India",
        "name": "Test User"
    }
    
    chat_history = []
    
    print("\n" + "="*70)
    print("TEST: Loan Conversation Flow - Agent Should Ask for Missing Details")
    print("="*70 + "\n")
    
    # Turn 1: User provides incomplete information
    message1 = "I have a gold loan of 5 lakhs"
    print(f"👤 USER: {message1}")
    
    response1 = await agent.invoke(
        message=message1,
        db=db,
        user_id=user_id,
        user_data=user_data,
        chat_history=chat_history
    )
    
    print(f"🤖 AGENT: {response1['response']}\n")
    
    # Check that NO loan was created yet
    loans_after_turn1 = db.query(DebtLoan).filter(DebtLoan.user_id == user_id).all()
    
    if loans_after_turn1:
        print("❌ FAIL: Agent created loan without asking for required details!")
        print(f"   Loan created with interest_rate={loans_after_turn1[0].interest_rate}%")
        print(f"   and monthly_payment={loans_after_turn1[0].monthly_payment}")
        return False
    else:
        print("✅ PASS: Agent did NOT create loan yet (waiting for details)")
    
    # Check that agent asked for missing information
    response_lower = response1['response'].lower()
    if any(keyword in response_lower for keyword in ['interest', 'rate', 'emi', 'payment', 'need', 'details']):
        print("✅ PASS: Agent asked for missing details\n")
    else:
        print("❌ FAIL: Agent didn't ask for required details\n")
        return False
    
    # Update chat history
    chat_history.append({"role": "user", "content": message1})
    chat_history.append({"role": "assistant", "content": response1['response']})
    
    # Turn 2: User provides missing details
    message2 = "12% interest rate, 15000 rupees per month EMI"
    print(f"👤 USER: {message2}")
    
    response2 = await agent.invoke(
        message=message2,
        db=db,
        user_id=user_id,
        user_data=user_data,
        chat_history=chat_history
    )
    
    print(f"🤖 AGENT: {response2['response']}\n")
    
    # Check that loan was NOW created with correct details
    loans_after_turn2 = db.query(DebtLoan).filter(DebtLoan.user_id == user_id).all()
    
    if not loans_after_turn2:
        print("❌ FAIL: Agent didn't create loan after receiving all details")
        return False
    
    loan = loans_after_turn2[0]
    print("="*70)
    print("LOAN CREATED:")
    print("="*70)
    print(f"Name: {loan.name}")
    print(f"Amount: ₹{loan.principal_amount:,.2f}")
    print(f"Interest Rate: {loan.interest_rate}%")
    print(f"Monthly Payment: ₹{loan.monthly_payment:,.2f}")
    print(f"Type: {loan.type.value}")
    print()
    
    # Validate loan details
    success = True
    if loan.principal_amount != 500000:
        print(f"❌ FAIL: Wrong amount (expected 500000, got {loan.principal_amount})")
        success = False
    else:
        print("✅ PASS: Correct amount (₹500,000)")
    
    if loan.interest_rate != 12.0:
        print(f"❌ FAIL: Wrong interest rate (expected 12.0, got {loan.interest_rate})")
        success = False
    else:
        print("✅ PASS: Correct interest rate (12%)")
    
    if loan.monthly_payment != 15000:
        print(f"❌ FAIL: Wrong monthly payment (expected 15000, got {loan.monthly_payment})")
        success = False
    else:
        print("✅ PASS: Correct monthly payment (₹15,000)")
    
    if "gold" not in loan.name.lower():
        print(f"❌ FAIL: Wrong loan name (expected 'gold loan', got '{loan.name}')")
        success = False
    else:
        print("✅ PASS: Correct loan name (contains 'gold')")
    
    # Cleanup
    db.rollback()
    db.close()
    
    print("\n" + "="*70)
    if success:
        print("✅ ALL TESTS PASSED - Agent correctly handles conversational loan flow")
    else:
        print("❌ SOME TESTS FAILED - See details above")
    print("="*70 + "\n")
    
    return success


async def test_loan_with_complete_info():
    """Test that agent handles complete loan info in one message"""
    
    db = next(get_db())
    user_id = str(uuid.uuid4())
    agent = get_financial_agent()
    
    user_data = {
        "timezone": "Asia/Kolkata",
        "currency": "INR",
        "country": "India",
        "name": "Test User"
    }
    
    print("\n" + "="*70)
    print("TEST: Complete Loan Info in One Message")
    print("="*70 + "\n")
    
    message = "I have a car loan of 10 lakhs at 9% interest, paying 20000 per month"
    print(f"👤 USER: {message}")
    
    response = await agent.invoke(
        message=message,
        db=db,
        user_id=user_id,
        user_data=user_data,
        chat_history=[]
    )
    
    print(f"🤖 AGENT: {response['response']}\n")
    
    # Check that loan was created immediately
    loans = db.query(DebtLoan).filter(DebtLoan.user_id == user_id).all()
    
    if not loans:
        print("❌ FAIL: Agent didn't create loan despite having all info")
        db.close()
        return False
    
    loan = loans[0]
    print("="*70)
    print("LOAN CREATED:")
    print("="*70)
    print(f"Name: {loan.name}")
    print(f"Amount: ₹{loan.principal_amount:,.2f}")
    print(f"Interest Rate: {loan.interest_rate}%")
    print(f"Monthly Payment: ₹{loan.monthly_payment:,.2f}")
    print()
    
    success = (
        loan.principal_amount == 1000000 and
        loan.interest_rate == 9.0 and
        loan.monthly_payment == 20000
    )
    
    if success:
        print("✅ PASS: Loan created correctly with all details")
    else:
        print("❌ FAIL: Loan details don't match input")
    
    db.rollback()
    db.close()
    
    print("="*70 + "\n")
    return success


async def main():
    """Run all tests"""
    print("\n" + "🧪 "*35)
    print("LOAN AGENT CONVERSATION TESTS")
    print("🧪 "*35 + "\n")
    
    test1_passed = await test_loan_conversation_flow()
    test2_passed = await test_loan_with_complete_info()
    
    print("\n" + "="*70)
    print("FINAL RESULTS:")
    print("="*70)
    print(f"Test 1 (Conversational Flow): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Complete Info): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
