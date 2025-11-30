#!/bin/bash
# Clean up legacy files and artifacts
# Usage: ./scripts/maintenance/cleanup-legacy.sh

set -e

echo "🧹 Cleaning up legacy files..."

# Remove old test scenario files
if [ -f "test_scenarios.sh" ]; then
    echo "🗑️  Removing test_scenarios.sh..."
    rm test_scenarios.sh
    echo "✅ Removed test_scenarios.sh"
fi

if [ -f "start.sh" ]; then
    echo "🗑️  Removing start.sh..."
    rm start.sh
    echo "✅ Removed start.sh"
fi

echo "✅ Cleanup complete!"
