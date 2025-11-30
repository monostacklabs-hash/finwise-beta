#!/bin/bash
# Remove deprecated files after migration
# Usage: ./scripts/maintenance/remove-deprecated-files.sh
# WARNING: This will delete old scripts and test files!

set -e

echo "⚠️  This will remove deprecated files from the root directory."
echo "   New organized files are in scripts/ and tests/ directories."
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

echo "🗑️  Removing deprecated scripts..."

# Remove old development scripts
rm -f run_python_app.sh
rm -f start_web_dev.sh
rm -f start_web.sh

# Remove old database scripts
rm -f apply_schema_descriptions.sh

# Remove old maintenance scripts
rm -f cleanup_legacy.sh

# Remove old test files
rm -f test_chat_agent.py
rm -f test_chat_diagnostic.py
rm -f test_chat_e2e.py
rm -f test_fallback.py
rm -f test_recurring_detection.py
rm -f test_session_handling.py

# Remove old test scripts
rm -f test_docker_db_reset.sh
rm -f test_recurring_update.sh
rm -f test_tier1_endpoints.sh
rm -f test_web_app_integration.sh

# Remove test databases from root (already moved to tests/fixtures/)
rm -f test_*.db
rm -f *.db

echo "✅ Cleanup complete!"
echo ""
echo "📝 All functionality is preserved in:"
echo "   - scripts/dev/       (development scripts)"
echo "   - scripts/db/        (database scripts)"
echo "   - scripts/maintenance/ (maintenance scripts)"
echo "   - tests/e2e/         (end-to-end tests)"
echo "   - tests/integration/ (integration tests)"
echo "   - tests/scripts/     (test runner scripts)"
echo ""
echo "See MIGRATION_GUIDE.md for the complete mapping."
