#!/bin/bash

# FinWise AI - Web App Integration Test Script

echo "🧪 FinWise AI Web App Integration Test"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to print test result
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((FAILED++))
    fi
}

# 1. Check if backend is running
echo "1. Checking backend status..."
curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1
test_result $? "Backend API is accessible"

# 2. Check if web dev server is running
echo ""
echo "2. Checking web dev server..."
curl -s http://localhost:5173 > /dev/null 2>&1
test_result $? "Web dev server is accessible"

# 3. Check TypeScript compilation
echo ""
echo "3. Checking TypeScript compilation..."
cd web
npx tsc --noEmit > /dev/null 2>&1
test_result $? "TypeScript compilation successful"

# 4. Run unit tests
echo ""
echo "4. Running unit tests..."
npm test > /tmp/test_output.txt 2>&1
if grep -q "17 passed" /tmp/test_output.txt; then
    test_result 0 "All unit tests passed (17/17)"
else
    test_result 1 "Unit tests failed"
    echo "   See /tmp/test_output.txt for details"
fi

# 5. Check for console errors in build
echo ""
echo "5. Checking build process..."
npm run build > /tmp/build_output.txt 2>&1
if [ $? -eq 0 ]; then
    test_result 0 "Production build successful"
else
    test_result 1 "Production build failed"
    echo "   See /tmp/build_output.txt for details"
fi

# 6. Check API endpoints
echo ""
echo "6. Testing API endpoints..."

# Test health endpoint
curl -s http://localhost:8000/api/v1/health | grep -q "healthy"
test_result $? "Health endpoint responding"

# Test docs endpoint
curl -s http://localhost:8000/docs > /dev/null 2>&1
test_result $? "API documentation accessible"

# 7. Check file structure
echo ""
echo "7. Verifying file structure..."

cd ..
FILES=(
    "web/src/App.tsx"
    "web/src/components/Dashboard.tsx"
    "web/src/components/Transactions.tsx"
    "web/src/components/Goals.tsx"
    "web/src/components/Debts.tsx"
    "web/src/components/Chat.tsx"
    "web/src/services/api.ts"
    "web/src/types/index.ts"
)

ALL_FILES_EXIST=0
for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "   Missing: $file"
        ALL_FILES_EXIST=1
    fi
done
test_result $ALL_FILES_EXIST "All required files exist"

# 8. Check test files
echo ""
echo "8. Verifying test files..."

TEST_FILES=(
    "web/src/test/Dashboard.test.tsx"
    "web/src/test/Transactions.test.tsx"
    "web/src/test/Goals.test.tsx"
    "web/e2e/auth.spec.ts"
    "web/e2e/dashboard.spec.ts"
    "web/e2e/transactions.spec.ts"
    "web/e2e/goals.spec.ts"
    "web/e2e/chat.spec.ts"
)

ALL_TESTS_EXIST=0
for file in "${TEST_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "   Missing: $file"
        ALL_TESTS_EXIST=1
    fi
done
test_result $ALL_TESTS_EXIST "All test files exist"

# Summary
echo ""
echo "======================================"
echo "Test Summary"
echo "======================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Web app is ready.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Please review the output above.${NC}"
    exit 1
fi
