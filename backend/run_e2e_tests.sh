#!/bin/bash
# End-to-End Test Runner Script

set -e

echo "=========================================="
echo "Financial Agent E2E Test Suite"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the backend directory or root
if [ -f "requirements.txt" ]; then
    # Running from root directory
    REQ_FILE="requirements.txt"
    TEST_PATH="backend/tests/test_e2e_complete.py"
elif [ -f "../requirements.txt" ]; then
    # Running from backend directory
    REQ_FILE="../requirements.txt"
    TEST_PATH="tests/test_e2e_complete.py"
else
    echo -e "${RED}Error: Cannot find requirements.txt${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r "$REQ_FILE"
pip install -q pytest pytest-cov

# Set environment variables for testing
if [ -f "requirements.txt" ]; then
    # Running from root - set PYTHONPATH to backend
    export PYTHONPATH=backend
else
    # Running from backend - set PYTHONPATH to current dir
    export PYTHONPATH=.
fi
export DATABASE_URL="sqlite:///./test_e2e.db"
export SECRET_KEY="test_secret_key_for_e2e_tests_only"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES=30
export CORS_ORIGINS='["http://localhost:3000"]'
export DEBUG=false

# Check if LLM API key is set
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Warning: No LLM API key found!${NC}"
    echo "Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable"
    echo "Tests may fail without a valid API key"
    echo ""
fi

# Clean up old test database
if [ -f "test_e2e.db" ]; then
    echo -e "${YELLOW}Cleaning up old test database...${NC}"
    rm test_e2e.db
fi

echo ""
echo "=========================================="
echo "Running E2E Tests"
echo "=========================================="
echo ""

# Run tests based on argument
case "${1:-all}" in
    "all")
        echo "Running all tests..."
        pytest "$TEST_PATH" -v -s
        ;;
    "quick")
        echo "Running quick tests (auth + one user journey)..."
        pytest "$TEST_PATH::test_01_authentication_flow" -v -s
        pytest "$TEST_PATH::test_04_average_user_journey" -v -s
        ;;
    "coverage")
        echo "Running tests with coverage report..."
        pytest "$TEST_PATH" -v --cov=app --cov-report=html --cov-report=term
        echo ""
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    "users")
        echo "Running user journey tests..."
        pytest "$TEST_PATH::test_02_rich_user_journey" -v -s
        pytest "$TEST_PATH::test_03_poor_user_journey" -v -s
        pytest "$TEST_PATH::test_04_average_user_journey" -v -s
        ;;
    "tools")
        echo "Running tool coverage test..."
        pytest "$TEST_PATH::test_19_all_tools_coverage" -v -s
        ;;
    "specific")
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please specify test name${NC}"
            echo "Usage: ./run_e2e_tests.sh specific test_name"
            exit 1
        fi
        echo "Running specific test: $2"
        pytest "$TEST_PATH::$2" -v -s
        ;;
    "help")
        echo "Usage: ./run_e2e_tests.sh [option]"
        echo ""
        echo "Options:"
        echo "  all       - Run all 20 tests (default)"
        echo "  quick     - Run auth + one user journey (fast)"
        echo "  coverage  - Run with coverage report"
        echo "  users     - Run all user journey tests"
        echo "  tools     - Run tool coverage test"
        echo "  specific  - Run specific test (requires test name)"
        echo "  help      - Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./run_e2e_tests.sh"
        echo "  ./run_e2e_tests.sh quick"
        echo "  ./run_e2e_tests.sh specific test_02_rich_user_journey"
        exit 0
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        echo "Run './run_e2e_tests.sh help' for usage"
        exit 1
        ;;
esac

TEST_EXIT_CODE=$?

# Clean up test database
if [ -f "test_e2e.db" ]; then
    rm test_e2e.db
fi

echo ""
echo "=========================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed${NC}"
fi
echo "=========================================="

exit $TEST_EXIT_CODE
