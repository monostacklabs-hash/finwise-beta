"""
Token Optimization Utilities - 2025 Industry Standards
Provides token counting, cost tracking, and optimization strategies
"""
import tiktoken
from typing import Dict, List, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage


# Token cost per 1K tokens (as of 2025) - Update these based on current pricing
TOKEN_COSTS = {
    # OpenAI
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    # Anthropic (with prompt caching)
    "claude-3-5-sonnet-20241022": {
        "input": 0.003,
        "output": 0.015,
        "cache_write": 0.00375,
        "cache_read": 0.0003,
    },
    "claude-3-5-haiku-20241022": {
        "input": 0.001,
        "output": 0.005,
        "cache_write": 0.00125,
        "cache_read": 0.0001,
    },
    "claude-3-opus-20240229": {
        "input": 0.015,
        "output": 0.075,
        "cache_write": 0.01875,
        "cache_read": 0.0015,
    },
    # Groq (free tier limits, minimal costs for paid)
    "llama-3.3-70b-versatile": {"input": 0.00059, "output": 0.00079},
    "llama-3.1-70b-versatile": {"input": 0.00059, "output": 0.00079},
    "mixtral-8x7b-32768": {"input": 0.00024, "output": 0.00024},
    # Grok (X.ai)
    "grok-beta": {"input": 0.002, "output": 0.01},
}

# Model context windows (max tokens)
CONTEXT_WINDOWS = {
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "claude-3-5-sonnet-20241022": 200000,
    "claude-3-5-haiku-20241022": 200000,
    "claude-3-opus-20240229": 200000,
    "llama-3.3-70b-versatile": 128000,
    "llama-3.1-70b-versatile": 128000,
    "mixtral-8x7b-32768": 32768,
    "grok-beta": 131072,
}


class TokenOptimizer:
    """
    2025 Industry Standard Token Optimizer
    Features: counting, cost tracking, adaptive context management
    """

    def __init__(self, model_name: Optional[str] = None):
        # Use a default model if None is provided
        if model_name is None:
            model_name = "claude-3-5-haiku-20241022"

        self.model_name = model_name
        self.encoding = self._get_encoding(model_name)
        self.context_window = CONTEXT_WINDOWS.get(model_name, 8000)
        self.costs = TOKEN_COSTS.get(model_name, {"input": 0.001, "output": 0.002})

    def _get_encoding(self, model_name: str):
        """Get appropriate tiktoken encoding for the model"""
        # For OpenAI models
        if "gpt-4" in model_name or "gpt-3.5" in model_name:
            return tiktoken.encoding_for_model("gpt-4")
        # For Claude/Anthropic - use cl100k_base (approximation)
        elif "claude" in model_name:
            return tiktoken.get_encoding("cl100k_base")
        # For others, use cl100k_base as default
        else:
            return tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string"""
        return len(self.encoding.encode(text))

    def count_message_tokens(self, messages: List[BaseMessage]) -> int:
        """Count tokens in a list of messages"""
        total_tokens = 0
        for message in messages:
            # Add message overhead (role, name, etc.) - typically 4 tokens per message
            total_tokens += 4
            # Add content tokens
            total_tokens += self.count_tokens(str(message.content))
        # Add 2 tokens for assistant reply priming
        total_tokens += 2
        return total_tokens

    def calculate_cost(
        self, input_tokens: int, output_tokens: int, cached_tokens: int = 0
    ) -> Dict[str, float]:
        """
        Calculate cost for token usage

        Returns:
            Dict with breakdown: input_cost, output_cost, cache_cost, total_cost
        """
        input_cost = (input_tokens / 1000) * self.costs.get("input", 0)
        output_cost = (output_tokens / 1000) * self.costs.get("output", 0)
        cache_cost = 0

        # If model supports caching (Anthropic)
        if "cache_read" in self.costs and cached_tokens > 0:
            cache_cost = (cached_tokens / 1000) * self.costs["cache_read"]
            # Reduce input cost by cached amount
            input_cost = ((input_tokens - cached_tokens) / 1000) * self.costs["input"]

        total_cost = input_cost + output_cost + cache_cost

        return {
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "cache_cost": round(cache_cost, 6),
            "total_cost": round(total_cost, 6),
            "currency": "USD",
        }

    def optimize_message_history(
        self,
        messages: List[BaseMessage],
        system_prompt_tokens: int,
        max_tokens_output: int = 2000,
        safety_margin: int = 500,
    ) -> List[BaseMessage]:
        """
        Adaptively manage context window - 2025 best practice

        Keeps messages within context limits by intelligently truncating history
        while preserving the most recent and important messages.

        Args:
            messages: List of conversation messages
            system_prompt_tokens: Tokens used by system prompt
            max_tokens_output: Maximum tokens for model output
            safety_margin: Safety buffer for token calculations

        Returns:
            Optimized message list that fits within context
        """
        # Calculate available tokens for messages
        available_tokens = (
            self.context_window - system_prompt_tokens - max_tokens_output - safety_margin
        )

        # If messages already fit, return as-is
        total_message_tokens = self.count_message_tokens(messages)
        if total_message_tokens <= available_tokens:
            return messages

        # Strategy: Keep most recent messages, remove oldest first
        # Always keep the last user message
        optimized = []
        current_tokens = 0

        # Start from the end (most recent)
        for message in reversed(messages):
            message_tokens = self.count_tokens(str(message.content)) + 4
            if current_tokens + message_tokens <= available_tokens:
                optimized.insert(0, message)
                current_tokens += message_tokens
            else:
                # Context window full
                break

        # Ensure we have at least the last message
        if not optimized and messages:
            optimized = [messages[-1]]

        return optimized

    def get_usage_stats(
        self, input_tokens: int, output_tokens: int, cached_tokens: int = 0
    ) -> Dict:
        """
        Get comprehensive usage statistics - for monitoring/analytics

        Returns:
            Detailed stats including tokens, costs, percentages
        """
        total_tokens = input_tokens + output_tokens
        cost_breakdown = self.calculate_cost(input_tokens, output_tokens, cached_tokens)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "model": self.model_name,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "cached": cached_tokens,
                "total": total_tokens,
            },
            "costs": cost_breakdown,
            "context_usage": {
                "used": total_tokens,
                "available": self.context_window,
                "percentage": round((total_tokens / self.context_window) * 100, 2),
            },
        }

    def should_use_caching(self) -> bool:
        """Check if model supports prompt caching (Anthropic Claude)"""
        return "cache_write" in self.costs

    def estimate_savings_with_cache(
        self, system_prompt_tokens: int, num_requests: int
    ) -> Dict:
        """
        Estimate cost savings with prompt caching (Anthropic)

        Args:
            system_prompt_tokens: Number of tokens in system prompt
            num_requests: Number of expected requests

        Returns:
            Savings breakdown
        """
        if not self.should_use_caching():
            return {"supported": False, "message": "Model does not support caching"}

        # First request: cache write
        first_request_cost = (system_prompt_tokens / 1000) * self.costs["cache_write"]

        # Subsequent requests: cache read
        subsequent_cost = (system_prompt_tokens / 1000) * self.costs["cache_read"]
        total_cached = first_request_cost + (subsequent_cost * (num_requests - 1))

        # Without caching
        no_cache_cost = (system_prompt_tokens / 1000) * self.costs["input"] * num_requests

        savings = no_cache_cost - total_cached
        savings_percentage = (savings / no_cache_cost) * 100 if no_cache_cost > 0 else 0

        return {
            "supported": True,
            "system_prompt_tokens": system_prompt_tokens,
            "num_requests": num_requests,
            "cost_with_cache": round(total_cached, 4),
            "cost_without_cache": round(no_cache_cost, 4),
            "savings": round(savings, 4),
            "savings_percentage": round(savings_percentage, 2),
            "currency": "USD",
        }
