"""
FastAPI Application - AI Financial Planner
Built with Python + FastAPI + LangGraph (2025 Industry Standards)
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .config import settings
from .database.session import init_db
from .api.routes import router

# Rate limiting (2025 optimization)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    limiter = Limiter(key_func=get_remote_address)
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    limiter = None

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="""
    🤖 **AI-Powered Financial Planning Agent**

    Built with 2025 industry standards:
    - **LangGraph** for autonomous agent orchestration
    - **LangChain** for AI tool integration
    - **FastAPI** for high-performance API
    - **PostgreSQL** for reliable data storage

    ## Primary Interface: `/chat`

    The `/chat` endpoint provides a natural language interface to your financial planner.
    The AI agent autonomously decides what actions to take based on your message.

    **Just chat naturally!** Examples:
    - "I spent $45 on groceries"
    - "What's my financial health?"
    - "How can I save more money?"
    - "I want to buy a house in 2 years, can I afford it?"

    ## Traditional REST Endpoints

    Traditional structured endpoints are available for programmatic access,
    but the chat interface is recommended for the best experience.

    ## Authentication

    All endpoints (except `/health`) require JWT authentication.
    1. Register: `POST /api/v1/auth/register`
    2. Login: `POST /api/v1/auth/login`
    3. Include the token: `Authorization: Bearer <token>`
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (2025 optimization)
if RATE_LIMITING_AVAILABLE and settings.RATE_LIMIT_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting AI Financial Planner...")
    print(f"📊 AI Provider: {settings.AI_PROVIDER}")

    # Show the active model for the current provider
    active_model = settings.get_model_for_provider(settings.AI_PROVIDER)
    print(f"🤖 Active Model: {active_model}")

    # Show fallback providers if configured
    if settings.fallback_providers:
        print(f"🔄 Fallback Providers: {', '.join(settings.fallback_providers)}")

    # Show optimization settings (2025)
    print(f"⚡ Prompt Caching: {'✅ Enabled' if settings.ENABLE_PROMPT_CACHING else '❌ Disabled'}")
    print(f"🛡️  Rate Limiting: {'✅ Enabled' if RATE_LIMITING_AVAILABLE and settings.RATE_LIMIT_ENABLED else '❌ Disabled'}")
    if RATE_LIMITING_AVAILABLE and settings.RATE_LIMIT_ENABLED:
        print(f"   └─ Limit: {settings.RATE_LIMIT_PER_MINUTE} requests/minute")
    print(f"💬 Max Chat History: {settings.MAX_CHAT_HISTORY_MESSAGES} messages")

    print(f"🔧 Debug Mode: {settings.DEBUG}")

    # Initialize database
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database initialization error: {e}")

    print("✅ Application started successfully!")
    print(f"📖 API Documentation: http://localhost:8000/docs")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🤖 AI Financial Planner API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
