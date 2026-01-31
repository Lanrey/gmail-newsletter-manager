#!/bin/bash
#
# Pre-Push Checklist Script
# Run this before pushing code to ensure quality standards
#
set -e

echo "🚀 Gmail Newsletter Manager - Pre-Push Checklist"
echo "================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        exit 1
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Ensure we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: Must run from project root directory${NC}"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Step 1: Check for uncommitted changes
echo ""
echo "1️⃣  Checking for uncommitted changes..."
if [ -n "$(git status --porcelain)" ]; then
    print_warning "You have uncommitted changes. Consider committing them first."
    git status --short
else
    print_status 0 "No uncommitted changes"
fi

# Step 2: Check for sensitive files
echo ""
echo "2️⃣  Checking for sensitive files..."
SENSITIVE_FILES=(
    "config.yaml"
    "*.db"
    "*.mbox"
    "*credentials*.json"
    "*.env"
    ".env"
)

for pattern in "${SENSITIVE_FILES[@]}"; do
    if git ls-files --error-unmatch $pattern 2>/dev/null; then
        print_status 1 "Sensitive file found in git: $pattern"
    fi
done
print_status 0 "No sensitive files in git"

# Step 3: Format code
echo ""
echo "3️⃣  Formatting code with black..."
black src tests --check --quiet
print_status $? "Code formatting check"

# Step 4: Sort imports
echo ""
echo "4️⃣  Sorting imports with isort..."
isort src tests --check-only --quiet
print_status $? "Import sorting check"

# Step 5: Lint with ruff
echo ""
echo "5️⃣  Linting with ruff..."
ruff check src tests --quiet
print_status $? "Ruff linting"

# Step 6: Lint with flake8
echo ""
echo "6️⃣  Linting with flake8..."
flake8 src tests --quiet
print_status $? "Flake8 linting"

# Step 7: Security check
echo ""
echo "7️⃣  Running security checks with bandit..."
bandit -r src -ll --quiet
print_status $? "Security check"

# Step 8: Run tests
echo ""
echo "8️⃣  Running tests..."
pytest tests/ -v --cov=newsletter_manager --cov-report=term-missing --quiet
TEST_RESULT=$?
if [ $TEST_RESULT -eq 0 ]; then
    print_status 0 "All tests passed"
else
    print_status 1 "Tests failed"
fi

# Step 9: Check test coverage
echo ""
echo "9️⃣  Checking test coverage..."
coverage report --fail-under=50 > /dev/null 2>&1
COVERAGE_RESULT=$?
if [ $COVERAGE_RESULT -eq 0 ]; then
    print_status 0 "Test coverage meets minimum threshold"
else
    print_warning "Test coverage below 50% (consider adding more tests)"
fi

# Step 10: Verify documentation
echo ""
echo "🔟 Verifying documentation..."
if [ ! -f "README.md" ]; then
    print_status 1 "README.md missing"
fi
if [ ! -f "LICENSE" ]; then
    print_status 1 "LICENSE missing"
fi
if [ ! -f "CONTRIBUTING.md" ]; then
    print_status 1 "CONTRIBUTING.md missing"
fi
if [ ! -f "SECURITY.md" ]; then
    print_status 1 "SECURITY.md missing"
fi
if [ ! -f "CHANGELOG.md" ]; then
    print_status 1 "CHANGELOG.md missing"
fi
print_status 0 "All required documentation present"

# Step 11: Build package
echo ""
echo "1️⃣1️⃣ Building package..."
python -m build --quiet > /dev/null 2>&1
BUILD_RESULT=$?
if [ $BUILD_RESULT -eq 0 ]; then
    print_status 0 "Package builds successfully"
    rm -rf dist/ build/ 2>/dev/null
else
    print_status 1 "Package build failed"
fi

# Final summary
echo ""
echo "================================================="
echo -e "${GREEN}✅ All checks passed! Ready to push.${NC}"
echo "================================================="
echo ""
echo "Next steps:"
echo "  1. git add <files>"
echo "  2. git commit -m 'Your message'"
echo "  3. git push origin <branch>"
echo ""
