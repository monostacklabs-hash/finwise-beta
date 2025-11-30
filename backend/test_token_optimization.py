#!/usr/bin/env python3
"""
Token Optimization Validation Test
Tests the 2025 prompt caching and token reduction optimizations
"""
import os
import sys
import time
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.database.session import SessionLocal, init_db
from app.database.models import User
from app.agents.financial_agent import get_financial_agent
from app.api.auth import hash_password

def create_test_user(db):
    """Create a test user"""
    email = f"test_token_{int(time.time())}@example.com"
    user = User(
        email=email,
        name="Token Test User",
        password=hash_password("testpass123"),
        timezone="America/New_York",
        currency="USD",
        country="US"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def format_token_stats(usage_stats):
    """Format token usage stats for display"""
    if not usage_stats:
        return "No usage stats available"

    tokens = usage_stats.get('tokens', {})
    costs = usage_stats.get('costs', {})

    return f"""
    Input Tokens:  {tokens.get('input', 0):,}
    Cached Tokens: {tokens.get('cached', 0):,}
    Output Tokens: {tokens.get('output', 0):,}
    Total Tokens:  {tokens.get('total', 0):,}
    Total Cost:    ${costs.get('total_cost', 0):.6f}
    """

def main():
    """Run token optimization validation tests"""
    print("=" * 80)
    print("🧪 TOKEN OPTIMIZATION VALIDATION TEST")
    print("=" * 80)
    print()

    # Check configuration
    print("📋 Configuration Check:")
    print(f"  AI Provider: {settings.AI_PROVIDER}")
    print(f"  AI Model: {settings.get_model_for_provider(settings.AI_PROVIDER)}")
    print(f"  Prompt Caching Enabled: {settings.ENABLE_PROMPT_CACHING}")
    print(f"  Token Tracking Enabled: {settings.ENABLE_TOKEN_TRACKING}")
    print(f"  Cost Tracking Enabled: {settings.ENABLE_COST_TRACKING}")
    print(f"  Max Chat History: {settings.MAX_CHAT_HISTORY_MESSAGES}")
    print()

    # Check API key
    if settings.AI_PROVIDER.lower() == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            print("❌ ANTHROPIC_API_KEY not set!")
            print("   Set it in .env file or environment variable")
            return 1
        print(f"  ✅ Anthropic API Key: {settings.ANTHROPIC_API_KEY[:10]}...")
    elif settings.AI_PROVIDER.lower() == "openai":
        if not settings.OPENAI_API_KEY:
            print("❌ OPENAI_API_KEY not set!")
            return 1
        print(f"  ✅ OpenAI API Key: {settings.OPENAI_API_KEY[:10]}...")

    print()
    print("-" * 80)
    print("🚀 Running Token Usage Test")
    print("-" * 80)
    print()

    # Initialize database and agent
    init_db()
    db = SessionLocal()

    try:
        # Create test user
        print("👤 Creating test user...")
        user = create_test_user(db)
        print(f"  ✅ User created: {user.email}")
        print()

        # Get agent
        agent = get_financial_agent()

        # Prepare user data
        user_data = {
            "timezone": user.timezone,
            "currency": user.currency,
            "country": user.country,
            "name": user.name,
        }

        # Test messages
        test_messages = [
            "What is my current balance?",
            "Add a transaction: I spent $50 on groceries",
            "Show me my recent transactions",
            "What is my financial health?",
            "Add another transaction: I earned $3000 salary"
        ]

        results = []
        chat_history = []

        print("💬 Sending test messages...")
        print()

        for i, message in enumerate(test_messages, 1):
            print(f"📨 Request {i}/{len(test_messages)}: {message[:50]}...")

            start_time = time.time()
            result = agent.sync_invoke(
                message=message,
                db=db,
                user_id=user.id,
                user_data=user_data,
                chat_history=chat_history
            )
            elapsed_time = time.time() - start_time

            # Extract usage stats
            usage_stats = result.get('usage', {})

            # Store result
            results.append({
                'request_num': i,
                'message': message,
                'response': result['response'][:100] + "..." if len(result['response']) > 100 else result['response'],
                'usage': usage_stats,
                'elapsed_time': elapsed_time,
                'success': result['success']
            })

            # Update chat history for next request
            chat_history.append({'role': 'user', 'content': message})
            chat_history.append({'role': 'assistant', 'content': result['response']})

            # Print summary
            if usage_stats:
                tokens = usage_stats.get('tokens', {})
                costs = usage_stats.get('costs', {})
                print(f"  ⏱️  Time: {elapsed_time:.2f}s")
                print(f"  🎫 Tokens: {tokens.get('total', 0):,} (input: {tokens.get('input', 0)}, cached: {tokens.get('cached', 0)}, output: {tokens.get('output', 0)})")
                print(f"  💰 Cost: ${costs.get('total_cost', 0):.6f}")

                # Highlight cache hits
                if tokens.get('cached', 0) > 0:
                    print(f"  ✅ CACHE HIT! Saved {tokens.get('cached', 0):,} tokens")
            else:
                print(f"  ⏱️  Time: {elapsed_time:.2f}s")
                print(f"  ⚠️  No usage stats available (token tracking may be disabled)")

            print()
            time.sleep(1)  # Small delay between requests

        # Analysis
        print()
        print("-" * 80)
        print("📊 ANALYSIS")
        print("-" * 80)
        print()

        # Calculate totals
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r['success'])

        total_tokens = 0
        total_input_tokens = 0
        total_cached_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0

        requests_with_cache = 0

        for r in results:
            usage = r.get('usage', {})
            if usage:
                tokens = usage.get('tokens', {})
                costs = usage.get('costs', {})

                total_tokens += tokens.get('total', 0)
                total_input_tokens += tokens.get('input', 0)
                total_cached_tokens += tokens.get('cached', 0)
                total_output_tokens += tokens.get('output', 0)
                total_cost += costs.get('total_cost', 0)

                if tokens.get('cached', 0) > 0:
                    requests_with_cache += 1

        print(f"📈 Overall Statistics:")
        print(f"  Total Requests: {total_requests}")
        print(f"  Successful: {successful_requests}")
        print(f"  Requests with Cache Hits: {requests_with_cache}")
        print()

        if total_tokens > 0:
            print(f"🎫 Token Usage:")
            print(f"  Total Tokens: {total_tokens:,}")
            print(f"  Input Tokens: {total_input_tokens:,}")
            print(f"  Cached Tokens: {total_cached_tokens:,} ⚡")
            print(f"  Output Tokens: {total_output_tokens:,}")
            print(f"  Average per Request: {total_tokens / total_requests:,.0f} tokens")
            print()

            print(f"💰 Cost Analysis:")
            print(f"  Total Cost: ${total_cost:.6f}")
            print(f"  Average per Request: ${total_cost / total_requests:.6f}")
            print()

            # Cache effectiveness
            if total_cached_tokens > 0:
                cache_percentage = (total_cached_tokens / (total_input_tokens + total_cached_tokens)) * 100
                print(f"⚡ Cache Effectiveness:")
                print(f"  Cache Hit Rate: {cache_percentage:.1f}%")
                print(f"  Tokens Saved via Cache: {total_cached_tokens:,}")
                print()

                # Estimate savings
                if settings.AI_PROVIDER.lower() == "anthropic":
                    # Anthropic Claude 3.5 Sonnet pricing
                    regular_cost_per_token = 0.003 / 1000  # $3 per million
                    cache_cost_per_token = 0.0003 / 1000   # $0.30 per million
                    savings = (regular_cost_per_token - cache_cost_per_token) * total_cached_tokens

                    print(f"💵 Estimated Savings:")
                    print(f"  Without Cache: ${(regular_cost_per_token * total_cached_tokens):.6f}")
                    print(f"  With Cache: ${(cache_cost_per_token * total_cached_tokens):.6f}")
                    print(f"  Savings: ${savings:.6f} ({((savings / (regular_cost_per_token * total_cached_tokens)) * 100):.1f}%)")
                    print()
        else:
            print("⚠️  No token usage data collected")
            print("   Make sure ENABLE_TOKEN_TRACKING=True and ENABLE_COST_TRACKING=True")
            print()

        # Validation
        print("-" * 80)
        print("✅ VALIDATION RESULTS")
        print("-" * 80)
        print()

        validation_passed = True

        # Check 1: All requests successful
        if successful_requests == total_requests:
            print("✅ All requests completed successfully")
        else:
            print(f"❌ {total_requests - successful_requests} requests failed")
            validation_passed = False

        # Check 2: Cache is working (for Anthropic)
        if settings.AI_PROVIDER.lower() == "anthropic" and settings.ENABLE_PROMPT_CACHING:
            if requests_with_cache >= 2:  # At least request 2+ should have cache hits
                print(f"✅ Prompt caching is working ({requests_with_cache} cache hits)")
            else:
                print(f"⚠️  Prompt caching may not be working (only {requests_with_cache} cache hits)")
                print("   Expected at least 2 cache hits for Anthropic with caching enabled")
                validation_passed = False

        # Check 3: Token tracking
        if total_tokens > 0:
            print("✅ Token tracking is working")
        else:
            print("⚠️  Token tracking not working or disabled")

        # Check 4: Average tokens per request (should be lower with optimizations)
        if total_tokens > 0:
            avg_tokens = total_tokens / total_requests
            # With caching, average should be significantly lower
            # Rough estimate: <3000 tokens per request is good
            if avg_tokens < 3000:
                print(f"✅ Average token usage is efficient ({avg_tokens:,.0f} per request)")
            else:
                print(f"⚠️  Average token usage is high ({avg_tokens:,.0f} per request)")
                print("   Expected <3000 tokens per request with optimizations")

        print()

        if validation_passed:
            print("🎉 All optimizations validated successfully!")
            return 0
        else:
            print("⚠️  Some validations failed. Review the results above.")
            return 1

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(main())
