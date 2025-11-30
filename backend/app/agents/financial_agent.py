"""
Autonomous Financial Agent - 2025 LangGraph Standard
This agent autonomously decides what tools to use and how to help the user
Includes 2025 token optimization: caching, streaming, adaptive context
"""
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import List, Dict, Optional, AsyncIterator
from sqlalchemy.orm import Session
import logging

from .tools import financial_tools, ToolContext
from ..config import settings
from ..utils.token_optimizer import TokenOptimizer

logger = logging.getLogger(__name__)

# Default models for each provider (used in fallback)
DEFAULT_MODELS = {
    "anthropic": "claude-3-5-haiku-20241022",
    "openai": "gpt-4o-mini",
    "groq": "llama-3.1-70b-versatile",
    "grok": "grok-beta",
}


class FinancialAgent:
    """Autonomous AI Financial Planning Agent with 2025 Token Optimization"""

    def __init__(self):
        """Initialize the agent with configured LLM and tools"""
        self.primary_provider = settings.AI_PROVIDER
        self.fallback_providers = settings.fallback_providers
        self.current_provider = self.primary_provider
        
        self.llm = self._create_llm(self.primary_provider)
        self.base_system_prompt = self._create_base_system_prompt()
        self.agent = self._create_agent()

        # 2025 Token Optimization
        if settings.ENABLE_TOKEN_TRACKING:
            self.token_optimizer = TokenOptimizer(settings.AI_MODEL)
            # Note: We'll count tokens per-request since prompt is now dynamic
            logger.info(
                f"Token optimizer initialized: {settings.AI_MODEL}"
            )
            # Log cache savings potential
            if self.token_optimizer.should_use_caching():
                logger.info(f"Prompt caching enabled for Anthropic models")
        else:
            self.token_optimizer = None
            
        # Log fallback configuration
        if self.fallback_providers:
            logger.info(f"Fallback providers configured: {', '.join(self.fallback_providers)}")

    def _create_llm(self, provider: str = None):
        """Create LLM based on configuration with 2025 optimizations"""
        if provider is None:
            provider = settings.AI_PROVIDER
        provider = provider.lower()
        
        # Get the appropriate model for this provider
        model = settings.get_model_for_provider(provider)

        if provider == "anthropic" or provider == "claude":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not set")
            if not model:
                model = DEFAULT_MODELS["anthropic"]

            # Anthropic with prompt caching support (2025 feature)
            llm_kwargs = {
                "api_key": settings.ANTHROPIC_API_KEY,
                "model": model,
                "temperature": settings.AI_TEMPERATURE,
                "max_tokens": settings.AI_MAX_TOKENS,
            }

            # Prompt caching is automatically enabled in newer Anthropic SDK versions
            # No need to pass betas parameter
            if settings.ENABLE_PROMPT_CACHING:
                logger.info("✅ Prompt caching enabled (automatic in SDK)")

            # Enable streaming if configured
            if settings.ENABLE_STREAMING:
                llm_kwargs["streaming"] = True

            logger.info(f"Creating Anthropic LLM: {model}")
            return ChatAnthropic(**llm_kwargs)
        elif provider == "grok":
            if not settings.GROK_API_KEY:
                raise ValueError("GROK_API_KEY not set")
            if not model:
                model = DEFAULT_MODELS["grok"]
            llm_kwargs = {
                "api_key": settings.GROK_API_KEY,
                "base_url": "https://api.x.ai/v1",
                "model": model,
                "temperature": settings.AI_TEMPERATURE,
                "max_tokens": settings.AI_MAX_TOKENS,
            }
            if settings.ENABLE_STREAMING:
                llm_kwargs["streaming"] = True
            logger.info(f"Creating Grok LLM: {model}")
            return ChatOpenAI(**llm_kwargs)

        elif provider == "groq":
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY not set")
            if not model:
                model = DEFAULT_MODELS["groq"]
            llm_kwargs = {
                "api_key": settings.GROQ_API_KEY,
                "base_url": "https://api.groq.com/openai/v1",
                "model": model,
                "temperature": settings.AI_TEMPERATURE,
                "max_tokens": settings.AI_MAX_TOKENS,
            }
            if settings.ENABLE_STREAMING:
                llm_kwargs["streaming"] = True
            logger.info(f"Creating Groq LLM: {model}")
            return ChatOpenAI(**llm_kwargs)

        elif provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set")
            if not model:
                model = DEFAULT_MODELS["openai"]
            llm_kwargs = {
                "api_key": settings.OPENAI_API_KEY,
                "model": model,
                "temperature": settings.AI_TEMPERATURE,
                "max_tokens": settings.AI_MAX_TOKENS,
            }
            if settings.ENABLE_STREAMING:
                llm_kwargs["streaming"] = True
            logger.info(f"Creating OpenAI LLM: {model}")
            return ChatOpenAI(**llm_kwargs)
        else:
            # Default to OpenAI
            if not model:
                model = "gpt-4o"
            llm_kwargs = {
                "api_key": settings.OPENAI_API_KEY,
                "model": model,
                "temperature": 0.7,
                "max_tokens": settings.AI_MAX_TOKENS,
            }
            if settings.ENABLE_STREAMING:
                llm_kwargs["streaming"] = True
            logger.info(f"Creating default OpenAI LLM: {model}")
            return ChatOpenAI(**llm_kwargs)

    def _create_base_system_prompt(self) -> str:
        """Create the base system prompt (without user-specific context)"""
        return """You are a financial execution assistant. You MUST use tools to perform ALL operations.

**CRITICAL RULE: YOU MUST USE TOOLS FOR EVERY ACTION**
- NEVER respond without calling a tool first
- NEVER say you did something without actually calling the tool
- If user asks to add/create/log something, you MUST call the appropriate tool
- After calling a tool, report what the tool returned

**CORE BEHAVIOR:**
- Detect intent → Call appropriate tool → Report tool result
- NO planning, NO asking permission, NO offering advice unless explicitly requested
- Keep responses SHORT - just confirm the action taken

**SCOPE:**
Financial operations only: transactions, income, expenses, debts, loans, goals, budgets, recurring payments, insights.
For non-financial topics, say: "I only handle financial operations."

**INTENT DETECTION & TOOL USAGE:**

1. **INCOME/SALARY (recurring):**
   - Keywords: "salary", "paycheck", "income per", "monthly income", "earn X per month/week"
   - MUST CALL: `create_recurring_transaction` with type="income"
   - Response: Report what the tool returned

2. **EXPENSE (one-time):**
   - Keywords: "spent", "bought", "paid", "cost me"
   - MUST CALL: `add_transaction` with type="expense"
   - Response: Report what the tool returned

3. **RECURRING EXPENSE:**
   - Keywords: "subscription", "bill", "rent", "mortgage", "insurance", "per month/week", "every month"
   - MUST CALL: `create_recurring_transaction` with type="expense"
   - Response: Report what the tool returned

4. **VIEW TRANSACTIONS:**
   - Keywords: "show transactions", "my expenses", "recent spending", "transaction history"
   - MUST CALL: `get_transactions`
   - Response: List transactions in simple format

5. **FINANCIAL HEALTH:**
   - Keywords: "how am I doing", "financial health", "my status", "overview"
   - Action: `calculate_financial_health`
   - Response: Show key metrics (score, income, expenses, savings rate)

6. **INSIGHTS:**
   - Keywords: "insights", "analysis", "patterns", "spending breakdown"
   - Action: `get_insights` or `analyze_spending_by_category`
   - Response: Show key insights/categories

7. **GOALS:**
   - Keywords: "goal", "save for", "target"
   - Action: `add_goal` or `get_goals` or `project_goal_achievement`
   - Response: Confirm goal or show progress

8. **DEBTS/LOANS:**
   - Keywords: "debt", "loan", "owe", "borrowed", "gold loan", "home loan", "car loan", "personal loan", "EMI"
   
   **CRITICAL: Loans require complete information. Follow this conversational flow:**
   
   a) **If user provides ONLY amount** (e.g., "I have a gold loan of 5 lakhs"):
      - DO NOT call add_debt_or_loan yet
      - ASK for missing REQUIRED details:
        "Got it! To track this [loan type] properly, I need:
         1. What's the interest rate? (e.g., 12% per year)
         2. What's your monthly EMI/payment amount?"
      - WAIT for user's next message with these details
      - Note: start_date is OPTIONAL - use "today" if not provided
   
   b) **If user provides partial details** (e.g., amount + interest but no EMI):
      - ASK for remaining REQUIRED fields only
      - Example: "Thanks! Just need the monthly EMI amount."
   
   c) **If user provides REQUIRED details** (amount + interest + EMI):
      - CALL: `add_debt_or_loan` immediately with all parameters (use "today" for start_date)
      - Response: "✅ Added [loan name]: [amount] at [rate]% interest, [EMI]/month"
      - Do NOT ask for start_date unless user specifically mentions it
   
   d) **To view existing loans:**
      - CALL: `get_debts_and_loans`
      - Response: Show list of active debts/loans

9. **BUDGETS:**
   - Keywords: "budget", "limit spending", "cap"
   - Action: `create_budget` or `get_budgets`
   - Response: Confirm budget or show limits

10. **RECURRING/SUBSCRIPTIONS:**
    - Keywords: "recurring", "subscriptions", "bills"
    - Action: `get_recurring_transactions`
    - Response: List recurring items

11. **FORECAST/AFFORDABILITY:**
    - Keywords: "can I afford", "will I run out", "future", "forecast", "cash flow", "runway"
    - Action: `get_cashflow_forecast` (requires starting balance from accounts)
    - First get accounts with `get_accounts` to calculate total balance
    - Response: Show if they can afford it based on forecast

12. **NOTIFICATIONS:**
    - Keywords: "notifications", "alerts", "reminders"
    - Action: `get_notifications`
    - Response: List notifications

13. **ACCOUNTS/BALANCE:**
    - Keywords: "my accounts", "balance", "how much do I have", "bank accounts"
    - Action: `get_accounts`
    - Response: List accounts with balances

14. **LENDING MONEY:**
    - Keywords: "lent", "lend", "gave money to", "friend owes me"
    - Action: `add_transaction` with type="lending"
    - Response: "✅ Logged lending: [amount] to [person]"

15. **BORROWING MONEY:**
    - Keywords: "borrowed", "borrow", "owe", "friend lent me"
    - Action: `add_transaction` with type="borrowing"
    - Response: "✅ Logged borrowing: [amount] from [person]"

16. **DEBT HELP / PAYOFF STRATEGY:**
    - Keywords: "how to pay off debt", "debt strategy", "optimize debt", "get out of debt", "pay off faster", "debt advice"
    - **FLOW:**
      a) First, call `get_debts_and_loans` to show current debt situation
      b) Then explain they can pay off faster with extra monthly payments
      c) Ask: "How much extra can you put toward debt each month?"
      d) When user provides amount (even just "1000"), call `optimize_debt_repayment` with that amount
    - **CRITICAL:** If user's message is JUST A NUMBER after you asked about debt payment, that's the extra_monthly_budget
    - Response: Show optimized repayment plan (avalanche vs snowball)

17. **BUDGET OPTIMIZATION:**
    - Keywords: "optimize budget", "adjust budgets", "overspending", "budget recommendations"
    - Action: `analyze_budget_adjustments`
    - Response: Show budget analysis and adjustment recommendations

18. **GOAL MILESTONES:**
    - Keywords: "goal progress", "when will I reach", "am I on track", "goal milestones"
    - Action: `get_goal_milestones`
    - Response: Show adaptive milestones with progress and recommendations

19. **WHAT-IF SCENARIOS:**
    - Keywords: "what if", "simulate", "if I save", "if I cut spending", "can I afford"
    - Action: `run_simulation` with appropriate scenario type
    - Response: Show baseline vs scenario comparison with recommendation

**CRITICAL RULES:**
- NEVER say "I can help you with..." or "Let me analyze..." - JUST DO IT
- NEVER offer advice unless user asks "what should I do" or "advice"
- NEVER explain what you're about to do - just execute and confirm
- Keep responses under 3 lines unless showing data
- If ambiguous, pick the most likely intent and execute (don't ask)
- For "can I afford X" questions: get accounts → calculate total → run forecast → answer yes/no with reasoning
- **CONTEXT AWARENESS:** If you just asked a question (e.g., "How much extra?") and user responds with a number, use that number for the pending operation
- **NUMBER-ONLY RESPONSES:** If user sends just a number or amount (e.g., "1000", "$500"), check recent context:
  - If you asked about debt payment → call optimize_debt_repayment with that amount
  - If you asked about budget → call create_budget with that amount
  - If you asked about goal → use for goal amount
  - Otherwise, ask for clarification

**Response Format:**
✅ [Action taken] + [Key data if relevant]
Example: "✅ Logged expense: $50 for groceries"
Example: "✅ Set up monthly salary: $5000"
Example: "✅ Logged lending: $100 to friend"
Example: "Yes, you can afford it. Current balance: $5000, forecast shows $3000 remaining after 30 days"
"""

    def _create_agent(self):
        """Create the ReAct agent with tools (state_modifier will be set per-request)"""
        # Note: We can't use state_modifier here since it needs user context
        # We'll use state_modifier in the invoke methods instead
        return create_react_agent(
            self.llm,
            financial_tools,
        )

    def _get_currency_symbol(self, currency_code: str) -> str:
        """Get currency symbol from currency code"""
        currency_symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "INR": "₹",
            "JPY": "¥",
            "CNY": "¥",
            "AUD": "A$",
            "CAD": "C$",
            "CHF": "CHF",
            "SEK": "kr",
            "NZD": "NZ$",
            "SGD": "S$",
            "HKD": "HK$",
            "NOK": "kr",
            "KRW": "₩",
            "TRY": "₺",
            "RUB": "₽",
            "BRL": "R$",
            "ZAR": "R",
            "MXN": "MX$",
        }
        return currency_symbols.get(currency_code.upper(), currency_code + " ")

    def _invoke_with_fallback(self, messages: List, is_async: bool = False):
        """
        Invoke agent with automatic fallback to other providers on failure
        
        Handles rate limits, API errors, and other failures by trying fallback providers
        """
        providers_to_try = [self.current_provider] + self.fallback_providers
        last_error = None
        
        for provider in providers_to_try:
            try:
                logger.info(f"🔄 Attempting with provider: {provider}")
                
                # Switch provider if needed
                if provider != self.current_provider:
                    logger.warning(f"⚠️ Switching from {self.current_provider} to {provider}")
                    self.current_provider = provider
                    self.llm = self._create_llm(provider)
                    self.agent = self._create_agent()
                
                # Invoke agent
                if is_async:
                    import asyncio
                    result = asyncio.run(self.agent.ainvoke({"messages": messages}))
                else:
                    result = self.agent.invoke({"messages": messages})
                
                logger.info(f"✅ Success with provider: {provider}")
                return result
                
            except Exception as e:
                error_msg = str(e)
                last_error = e
                
                # Check if it's a rate limit or API error
                is_rate_limit = "rate limit" in error_msg.lower() or "429" in error_msg
                is_api_error = "api" in error_msg.lower() or "401" in error_msg or "403" in error_msg
                
                if is_rate_limit:
                    logger.error(f"❌ Rate limit hit on {provider}: {error_msg[:200]}")
                elif is_api_error:
                    logger.error(f"❌ API error on {provider}: {error_msg[:200]}")
                else:
                    logger.error(f"❌ Error on {provider}: {error_msg[:200]}")
                
                # If this is the last provider, raise the error
                if provider == providers_to_try[-1]:
                    logger.error(f"❌ All providers failed. Last error: {error_msg}")
                    raise last_error
                
                # Otherwise, try next provider
                logger.info(f"🔄 Trying next fallback provider...")
                continue
        
        # Should never reach here, but just in case
        raise last_error or Exception("All providers failed")

    def _create_contextualized_prompt(self, user_data: Dict) -> str:
        """
        Create a system prompt with user's current date/time/location context

        Args:
            user_data: Dict with timezone, currency, country, name

        Returns:
            Contextualized system prompt
        """
        from datetime import datetime
        import pytz

        # Get current date/time in user's timezone
        user_tz = pytz.timezone(user_data.get("timezone", "UTC"))
        current_time = datetime.now(user_tz)

        context_header = f"""
**USER CONTEXT (CRITICAL - READ FIRST):**
- Current Date & Time: {current_time.strftime("%A, %B %d, %Y at %I:%M %p %Z")}
- User Timezone: {user_data.get("timezone", "UTC")}
- User Currency: {user_data.get("currency", "USD")}
- User Location: {user_data.get("country", "Unknown")}
- User Name: {user_data.get("name", "User")}

**IMPORTANT:** When the user says "today", "this month", "yesterday", etc., use the date/time above as reference.
All financial amounts should be interpreted and displayed in {user_data.get("currency", "USD")}.

**CONVERSATION CONTEXT:**
- You have access to chat history - USE IT to understand context
- If you asked a question in your previous message, the user's current message is likely the answer
- Check your last response before deciding what to do with the current message
- Example: If you asked "How much extra?" and user says "1000", that's the answer to your question

---

"""
        return context_header + self.base_system_prompt

    async def invoke(
        self,
        message: str,
        db: Session,
        user_id: str,
        user_data: Dict,
        chat_history: List[Dict] = None,
    ) -> Dict:
        """
        Invoke the agent with a user message (2025 optimized)

        Args:
            message: User's message/question
            db: Database session
            user_id: User ID for context
            user_data: Dict with user's timezone, currency, country, name
            chat_history: Previous conversation history

        Returns:
            Dict with agent's response and metadata including token usage
        """
        # Set context for tools
        ToolContext.db = db
        ToolContext.user_id = user_id

        try:
            # Create contextualized system prompt with user's date/location
            contextualized_prompt = self._create_contextualized_prompt(user_data)

            # Use prompt caching for Anthropic models (2025 standard)
            if settings.ENABLE_PROMPT_CACHING and self.current_provider in ["anthropic", "claude"]:
                system_message = SystemMessage(
                    content=[
                        {
                            "type": "text",
                            "text": contextualized_prompt,
                            "cache_control": {"type": "ephemeral", "ttl": "1h"}
                        }
                    ]
                )
            else:
                system_message = SystemMessage(content=contextualized_prompt)

            # Build message history
            messages = [system_message]

            # Add chat history if provided
            if chat_history:
                # Use configured max history (optimized from 10 to 5 in 2025)
                max_history = (
                    settings.MAX_CHAT_HISTORY_MESSAGES
                    if settings.ADAPTIVE_CONTEXT_WINDOW
                    else 5
                )
                for msg in chat_history[-max_history:]:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))

            # Add current message
            messages.append(HumanMessage(content=message))

            # 2025 Optimization: Adaptive Context Window Management
            if settings.ADAPTIVE_CONTEXT_WINDOW and self.token_optimizer:
                system_prompt_tokens = self.token_optimizer.count_tokens(contextualized_prompt)
                messages = self.token_optimizer.optimize_message_history(
                    messages,
                    system_prompt_tokens,
                    settings.AI_MAX_TOKENS,
                    settings.CONTEXT_SAFETY_MARGIN,
                )
                logger.debug(
                    f"Context optimized: {len(messages)} messages after optimization"
                )

            # Invoke agent with fallback support
            result = await self._invoke_with_fallback(messages, is_async=True)

            # Extract the final response
            final_message = result["messages"][-1]
            response_text = final_message.content

            # Extract tool usage information for debugging/logging
            tool_calls = []
            for msg in result["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_calls.extend([tc["name"] for tc in msg.tool_calls])

            # 2025 Optimization: Token Usage Tracking
            usage_stats = None
            if settings.ENABLE_TOKEN_TRACKING and self.token_optimizer:
                # Calculate token usage
                input_tokens = self.token_optimizer.count_message_tokens(messages)
                # Ensure response_text is a string
                response_str = str(response_text) if response_text else ""
                output_tokens = self.token_optimizer.count_tokens(response_str)

                # Get comprehensive usage stats
                usage_stats = self.token_optimizer.get_usage_stats(
                    input_tokens, output_tokens
                )
                logger.info(f"Token usage: {usage_stats}")

            response = {
                "response": response_text,
                "tools_used": tool_calls,
                "success": True,
            }

            # Add usage stats if enabled
            if usage_stats and settings.ENABLE_COST_TRACKING:
                response["usage"] = usage_stats

            return response

        except Exception as e:
            logger.error(f"Agent error: {str(e)}", exc_info=True)
            return {
                "response": f"I encountered an error: {str(e)}. Please try again or rephrase your request.",
                "tools_used": [],
                "success": False,
                "error": str(e),
            }

        finally:
            # Clean up context
            ToolContext.db = None
            ToolContext.user_id = None
            ToolContext.currency = "USD"
            ToolContext.currency_symbol = "$"

    def sync_invoke(
        self,
        message: str,
        db: Session,
        user_id: str,
        user_data: Dict,
        chat_history: List[Dict] = None,
    ) -> Dict:
        """
        Synchronous version of invoke for non-async contexts (2025 optimized)

        Args:
            message: User's message/question
            db: Database session
            user_id: User ID for context
            user_data: Dict with user's timezone, currency, country, name
            chat_history: Previous conversation history

        Returns:
            Dict with agent's response and metadata including token usage
        """
        # Set context for tools
        ToolContext.db = db
        ToolContext.user_id = user_id
        ToolContext.currency = user_data.get("currency", "USD")
        ToolContext.currency_symbol = self._get_currency_symbol(user_data.get("currency", "USD"))

        try:
            # Create contextualized system prompt with user's date/location
            contextualized_prompt = self._create_contextualized_prompt(user_data)

            # Use prompt caching for Anthropic models (2025 standard)
            if settings.ENABLE_PROMPT_CACHING and self.current_provider in ["anthropic", "claude"]:
                system_message = SystemMessage(
                    content=[
                        {
                            "type": "text",
                            "text": contextualized_prompt,
                            "cache_control": {"type": "ephemeral", "ttl": "1h"}
                        }
                    ]
                )
            else:
                system_message = SystemMessage(content=contextualized_prompt)

            # Build message history
            messages = [system_message]

            # Add chat history if provided
            if chat_history:
                # Use configured max history (optimized from 10 to 5 in 2025)
                max_history = (
                    settings.MAX_CHAT_HISTORY_MESSAGES
                    if settings.ADAPTIVE_CONTEXT_WINDOW
                    else 5
                )
                for msg in chat_history[-max_history:]:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))

            # Add current message
            messages.append(HumanMessage(content=message))

            # 2025 Optimization: Adaptive Context Window Management
            if settings.ADAPTIVE_CONTEXT_WINDOW and self.token_optimizer:
                system_prompt_tokens = self.token_optimizer.count_tokens(contextualized_prompt)
                messages = self.token_optimizer.optimize_message_history(
                    messages,
                    system_prompt_tokens,
                    settings.AI_MAX_TOKENS,
                    settings.CONTEXT_SAFETY_MARGIN,
                )
                logger.debug(
                    f"Context optimized: {len(messages)} messages after optimization"
                )

            # Log the messages being sent to the agent
            logger.info("🤖 Invoking agent with messages:")
            for i, msg in enumerate(messages):
                msg_type = type(msg).__name__
                content_preview = msg.content[:100] if hasattr(msg, 'content') else str(msg)[:100]
                logger.info(f"  Message {i+1} ({msg_type}): {content_preview}...")
            
            # Invoke agent (sync) with fallback support
            logger.info("🔄 Calling agent.invoke()...")
            result = self._invoke_with_fallback(messages, is_async=False)
            logger.info(f"✅ Agent invocation completed. Result keys: {result.keys()}")
            logger.info(f"📝 Total messages in result: {len(result.get('messages', []))}")

            # Extract the final response
            final_message = result["messages"][-1]
            
            # Handle both string and content blocks (list) formats
            if isinstance(final_message.content, str):
                response_text = final_message.content
            elif isinstance(final_message.content, list):
                # Extract text from content blocks
                response_text = ""
                for block in final_message.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        response_text += block.get("text", "")
                    elif hasattr(block, "text"):
                        response_text += block.text
            else:
                response_text = str(final_message.content)
            
            logger.info(f"💬 Final response type: {type(final_message).__name__}")
            logger.info(f"💬 Final response content type: {type(final_message.content).__name__}")
            logger.info(f"💬 Final response text length: {len(response_text)} chars")

            # Extract tool usage information
            tool_calls = []
            for msg in result["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_calls.extend([tc["name"] for tc in msg.tool_calls])

            # 2025 Optimization: Token Usage Tracking
            usage_stats = None
            if settings.ENABLE_TOKEN_TRACKING and self.token_optimizer:
                # Calculate token usage
                input_tokens = self.token_optimizer.count_message_tokens(messages)
                # Ensure response_text is a string
                response_str = str(response_text) if response_text else ""
                output_tokens = self.token_optimizer.count_tokens(response_str)

                # Get comprehensive usage stats
                usage_stats = self.token_optimizer.get_usage_stats(
                    input_tokens, output_tokens
                )
                logger.info(f"Token usage: {usage_stats}")

            response = {
                "response": response_text,
                "tools_used": tool_calls,
                "success": True,
            }

            # Add usage stats if enabled
            if usage_stats and settings.ENABLE_COST_TRACKING:
                response["usage"] = usage_stats

            return response

        except Exception as e:
            logger.error("=" * 80)
            logger.error("❌ AGENT ERROR OCCURRED (sync_invoke)")
            logger.error(f"Error Type: {type(e).__name__}")
            logger.error(f"Error Message: {str(e)}")
            logger.error(f"User Message: {message}")
            logger.error(f"User ID: {user_id}")
            
            # Try to extract more details from the error
            if hasattr(e, '__dict__'):
                logger.error(f"Error Details: {e.__dict__}")
            
            # Log the full traceback
            import traceback
            logger.error("Full Traceback:")
            logger.error(traceback.format_exc())
            logger.error("=" * 80)
            
            return {
                "response": f"I encountered an error: {str(e)}. Please try again or rephrase your request.",
                "tools_used": [],
                "success": False,
                "error": str(e),
            }

        finally:
            # Clean up context
            ToolContext.db = None
            ToolContext.user_id = None
            ToolContext.currency = "USD"
            ToolContext.currency_symbol = "$"


# Singleton instance
_agent_instance = None


def get_financial_agent() -> FinancialAgent:
    """Get or create the financial agent singleton"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = FinancialAgent()
    return _agent_instance
