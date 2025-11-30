# AI Financial Planner

Autonomous AI financial planning agent built with Python, FastAPI, and LangGraph.

## Quick Start

### Backend API
```bash
# Start the backend
./scripts/dev/start-backend.sh
```

Visit http://localhost:8000/docs for interactive API documentation.

### Web Application
```bash
# Start the web app (requires backend running)
./scripts/dev/start-web.sh
```

Visit http://localhost:5173 for the web interface.

> **Note**: Old scripts (`./run_python_app.sh`, `./start_web_dev.sh`) are deprecated. See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for new paths.

## Documentation

### Backend
- **[QUICKSTART_ADVANCED.md](./QUICKSTART_ADVANCED.md)** - 5-minute guide to advanced features
- **[ADVANCED_FEATURES.md](./ADVANCED_FEATURES.md)** - Complete guide to AI-powered budgeting and forecasting
- **[JOURNAL.md](./JOURNAL.md)** - Development log and technical documentation
- **[FEATURE_SUMMARY.md](./FEATURE_SUMMARY.md)** - Implementation summary and checklist

### Web Application
- **[web/README.md](./web/README.md)** - Web app documentation and setup
- **[WEB_APP_IMPLEMENTATION_SUMMARY.md](./WEB_APP_IMPLEMENTATION_SUMMARY.md)** - Complete implementation details
- **[web/TEST_INTEGRATION.md](./web/TEST_INTEGRATION.md)** - Integration testing guide

## What This Does

Chat naturally with your AI financial advisor:

```
You: "I spent $45 on groceries"
AI:  ✅ Added $45 expense in food category.
     Based on your spending, you're at 35% of your monthly budget.
```

The AI agent autonomously:
- Tracks income and expenses
- Manages debts and loans
- Sets and monitors financial goals
- Calculates financial health
- Optimizes debt repayment
- Analyzes spending patterns

## TIER 1 Features (2025)

**Smart Notifications System**
- Budget alerts when approaching/exceeding limits
- Bill reminders for recurring transactions
- Goal milestone celebrations (25%, 50%, 75%, 100%)
- Unusual spending detection
- Debt payoff celebrations

**Budget Management**
- Track spending vs budget by category
- Monthly, weekly, or yearly periods
- Automatic overspending alerts
- Real-time budget status

**Recurring Transactions**
- Schedule bills and subscriptions
- Auto-add transactions on due date
- Bill reminders X days before
- Support for daily, weekly, monthly, quarterly, yearly frequencies

**Cash Flow Forecasting**
- Project future balance based on recurring transactions
- 90-day forecast by default
- Identify potential shortfalls

**Mobile App**
- React Native iOS/Android app
- Full feature parity with backend
- Modern UI with dark mode support

**Data Management**
- Flush all data (start fresh, keep account)
- Delete account (permanent removal)
- Multiple confirmations for safety
- GDPR/CCPA compliance

## Advanced Features (2025)

**Dynamic Budgeting**
- AI-powered budget adjustments based on spending behavior
- Cross-category optimization (reduce discretionary when overspending)
- Goal-priority-based reallocation
- Distinguishes essential vs discretionary spending
- Actionable recommendations with reasoning

**Hierarchical Categories**
- Multi-level category structure (e.g., Home > Groceries > Fresh Produce)
- 9 root categories with 50+ subcategories
- Smart category suggestions from transaction descriptions
- Full path tracking and parent-child relationships

**AI-Adjusted Goal Milestones**
- Adaptive milestones that adjust to your savings rate
- 25%, 50%, 75%, 100% progress tracking
- On-track vs behind status detection
- Personalized recommendations per goal
- Savings rate analysis and benchmarking

**Financial Simulations**
- What-if scenario modeling for decision-making
- Simulate income changes, expense cuts, new subscriptions
- Baseline vs scenario comparison
- 180-day forecasts with impact analysis
- Actionable recommendations

## Technology Stack

- **Python 3.11+** - Modern, type-safe
- **FastAPI** - High-performance async web framework
- **LangGraph** - Autonomous agent orchestration
- **Anthropic Claude** - AI model (configurable: OpenAI, Grok)
- **PostgreSQL** - Reliable data persistence
- **Docker** - Easy deployment

## Current Configuration

- AI Provider: Anthropic Claude
- Model: claude-3-5-sonnet-20240620
- Database: PostgreSQL 15
- API Port: 8000

## Development

### Database Reset on Startup

For development, you can configure Docker to drop and recreate the database on each startup:

```bash
# Set environment variable
RESET_DB_ON_STARTUP=true docker compose -f docker-compose.python.yml up

# Or add to .env file
echo "RESET_DB_ON_STARTUP=true" >> .env
docker compose -f docker-compose.python.yml up
```

**Note**: This destroys all data. Default is `false` for safety. Categories are automatically seeded when users register.

### Manual Database Reset

```bash
# Interactive reset (requires confirmation)
./scripts/db/reset-db.sh

# Automated reset (no confirmation)
./scripts/db/reset-db-auto.sh
```

## Project Structure

```
fin-agent/
├── backend/              # Python FastAPI backend
├── web/                  # React web application
├── mobile/               # React Native mobile app
├── scripts/              # Utility scripts (dev, db, maintenance)
├── tests/                # Organized test suite (e2e, integration)
├── examples/             # Example code and demos
└── docs/                 # Documentation
```

See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for details on the new organization.

## License

MIT License
