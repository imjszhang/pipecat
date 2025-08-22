#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "🔍 Running pre-commit checks..."

# Change to project root (one level up from scripts/)
cd "$(dirname "$0")/.."

# Format check
echo "📝 Checking code formatting..."
if ! NO_COLOR=1 ruff format --diff --check; then
    echo -e "${RED}❌ Code formatting issues found. Run 'ruff format' to fix.${NC}"
    exit 1
fi

# Lint check
echo "🔍 Running linter..."
if ! ruff check; then
    echo -e "${RED}❌ Linting issues found.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All pre-commit checks passed!${NC}"