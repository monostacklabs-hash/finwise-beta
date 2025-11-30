#!/bin/bash
# Verify the new file organization
# Usage: ./scripts/maintenance/verify-organization.sh

set -e

echo "🔍 Verifying Project Organization"
echo "=================================="
echo ""

# Check scripts directory
echo "📁 Scripts Directory:"
echo "  Dev scripts: $(ls -1 scripts/dev/*.sh 2>/dev/null | wc -l | tr -d ' ')"
echo "  DB scripts: $(ls -1 scripts/db/*.sh 2>/dev/null | wc -l | tr -d ' ')"
echo "  Maintenance: $(ls -1 scripts/maintenance/*.sh 2>/dev/null | wc -l | tr -d ' ')"
echo ""

# Check tests directory
echo "📁 Tests Directory:"
echo "  E2E chat tests: $(ls -1 tests/e2e/chat/*.py 2>/dev/null | wc -l | tr -d ' ')"
echo "  E2E transaction tests: $(ls -1 tests/e2e/transactions/*.py 2>/dev/null | wc -l | tr -d ' ')"
echo "  E2E provider tests: $(ls -1 tests/e2e/providers/*.py 2>/dev/null | wc -l | tr -d ' ')"
echo "  Integration tests: $(ls -1 tests/integration/*.py 2>/dev/null | wc -l | tr -d ' ')"
echo "  Test scripts: $(ls -1 tests/scripts/*.sh 2>/dev/null | wc -l | tr -d ' ')"
echo ""

# Check for deprecated files in root
echo "⚠️  Deprecated Files in Root:"
DEPRECATED_COUNT=0
for file in run_python_app.sh start_web_dev.sh start_web.sh apply_schema_descriptions.sh \
            cleanup_legacy.sh test_*.py test_*.sh test_*.db; do
    if [ -f "$file" ]; then
        echo "  - $file"
        ((DEPRECATED_COUNT++))
    fi
done

if [ $DEPRECATED_COUNT -eq 0 ]; then
    echo "  ✅ None found (clean root)"
else
    echo ""
    echo "  Run ./scripts/maintenance/remove-deprecated-files.sh to clean up"
fi
echo ""

# Check documentation
echo "📚 Documentation:"
[ -f "MIGRATION_GUIDE.md" ] && echo "  ✅ MIGRATION_GUIDE.md" || echo "  ❌ MIGRATION_GUIDE.md missing"
[ -f "PROJECT_STRUCTURE.md" ] && echo "  ✅ PROJECT_STRUCTURE.md" || echo "  ❌ PROJECT_STRUCTURE.md missing"
[ -f "scripts/README.md" ] && echo "  ✅ scripts/README.md" || echo "  ❌ scripts/README.md missing"
[ -f "tests/README.md" ] && echo "  ✅ tests/README.md" || echo "  ❌ tests/README.md missing"
echo ""

# Check permissions
echo "🔐 Script Permissions:"
EXECUTABLE_COUNT=$(find scripts tests/scripts -name "*.sh" -perm +111 2>/dev/null | wc -l | tr -d ' ')
TOTAL_SCRIPTS=$(find scripts tests/scripts -name "*.sh" 2>/dev/null | wc -l | tr -d ' ')
echo "  Executable: $EXECUTABLE_COUNT / $TOTAL_SCRIPTS"

if [ "$EXECUTABLE_COUNT" -eq "$TOTAL_SCRIPTS" ]; then
    echo "  ✅ All scripts are executable"
else
    echo "  ⚠️  Some scripts may need chmod +x"
fi
echo ""

echo "✅ Verification complete!"
