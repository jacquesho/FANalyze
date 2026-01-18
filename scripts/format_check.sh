#!/bin/bash
# Quick format check script - run before committing
# Usage: ./scripts/format_check.sh

set -e

echo "🔍 Running format check..."
uv run ruff format --check .

echo "✅ Formatting check passed!"
echo ""
echo "💡 Tip: Run 'uv run ruff format .' to auto-fix formatting issues"
