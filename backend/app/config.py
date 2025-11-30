"""
Application Configuration
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field
from typing import Optional, Union, List
import os


class Settings(BaseSettings):
    """Application settings from environment variables"""
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_parse_none_str='null',
        extra='ignore'  # Allow extra fields during testing
    )

    # Add environment support
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')

    # Application
    APP_NAME: str = "AI Financial Planner"
    VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/financial_planner"

    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AI Provider Configuration
    AI_PROVIDER: str = "openai"  # openai, anthropic, grok, or groq
    AI_FALLBACK_PROVIDERS: str = ""  # Comma-separated list of fallback providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GROK_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # AI Model Configuration - Provider-specific models
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-20241022"
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    GROK_MODEL: str = "grok-beta"
    
    # Legacy support - falls back to provider-specific model if not set
    AI_MODEL: Optional[str] = None
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 2000
    
    @property
    def fallback_providers(self) -> List[str]:
        """Parse fallback providers from comma-separated string"""
        if not self.AI_FALLBACK_PROVIDERS:
            return []
        return [p.strip() for p in self.AI_FALLBACK_PROVIDERS.split(',') if p.strip()]
    
    def get_model_for_provider(self, provider: str) -> str:
        """Get the appropriate model for a given provider with logging"""
        import logging
        logger = logging.getLogger(__name__)
        
        provider = provider.lower()
        
        # If legacy AI_MODEL is set, use it (backward compatibility)
        if self.AI_MODEL:
            logger.info(f"Using legacy AI_MODEL: {self.AI_MODEL} for provider: {provider}")
            return self.AI_MODEL
        
        # Map provider to model
        model_map = {
            "openai": self.OPENAI_MODEL,
            "anthropic": self.ANTHROPIC_MODEL,
            "claude": self.ANTHROPIC_MODEL,
            "groq": self.GROQ_MODEL,
            "grok": self.GROK_MODEL,
        }
        
        model = model_map.get(provider)
        if model:
            logger.info(f"✓ Provider '{provider}' → Model '{model}'")
            return model
        
        # Fallback to OpenAI model as default
        logger.warning(f"Unknown provider '{provider}', falling back to OpenAI model: {self.OPENAI_MODEL}")
        return self.OPENAI_MODEL

    # 2025 Token Optimization Settings
    ENABLE_TOKEN_TRACKING: bool = True
    ENABLE_COST_TRACKING: bool = True
    ENABLE_PROMPT_CACHING: bool = True  # For Anthropic Claude models
    ENABLE_STREAMING: bool = True
    ADAPTIVE_CONTEXT_WINDOW: bool = True
    MAX_CHAT_HISTORY_MESSAGES: int = 5  # Reduced from 10 to optimize token usage
    CONTEXT_SAFETY_MARGIN: int = 500  # Token buffer for safety

    # Rate Limiting Settings (2025)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 20  # Requests per minute per user

    # Redis (optional for caching)
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    USE_REDIS: bool = False

    # CORS - use string type to avoid JSON parsing issues
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    @field_validator('CORS_ORIGINS', mode='after')
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        """Parse CORS_ORIGINS from comma-separated string to list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v


settings = Settings()
