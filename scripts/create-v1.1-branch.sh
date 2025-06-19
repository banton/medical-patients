#!/bin/bash
# Script to create v1.1 consolidated feature branch

set -e  # Exit on error

echo "=== Creating v1.1 Consolidated Feature Branch ==="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "config.py" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    exit 1
fi

# 1. Ensure we have latest main
echo -e "${YELLOW}Updating main branch...${NC}"
git checkout main
git pull origin main

# 2. Create or update develop branch
echo -e "${YELLOW}Setting up develop branch...${NC}"
if git show-ref --verify --quiet refs/heads/develop; then
    git checkout develop
    git merge main --no-edit
else
    git checkout -b develop
fi

# 3. Create v1.1 feature branch
echo -e "${YELLOW}Creating feature/v1.1-consolidated branch...${NC}"
git checkout -b feature/v1.1-consolidated

# 4. Merge EPICs in order
echo -e "${GREEN}=== Merging EPIC-001: Cross-platform dev environment ===${NC}"
git merge origin/epic/cross-platform-dev-env --no-ff -m "feat(v1.1): merge EPIC-001 cross-platform dev environment" || {
    echo -e "${RED}Merge conflict in EPIC-001. Resolve conflicts and run: git merge --continue${NC}"
    exit 1
}

echo -e "${GREEN}=== Merging EPIC-002: API key management ===${NC}"
git merge origin/epic/api-key-management --no-ff -m "feat(v1.1): merge EPIC-002 API key management" || {
    echo -e "${RED}Merge conflict in EPIC-002. Resolve conflicts and run: git merge --continue${NC}"
    exit 1
}

echo -e "${GREEN}=== Merging EPIC-003: Production scalability ===${NC}"
git merge origin/epic/production-scalability --no-ff -m "feat(v1.1): merge EPIC-003 production scalability" || {
    echo -e "${RED}Merge conflict in EPIC-003. Resolve conflicts and run: git merge --continue${NC}"
    exit 1
}

echo -e "${GREEN}=== Merging EPIC-006: Memory management ===${NC}"
git merge origin/epic/memory-management --no-ff -m "feat(v1.1): merge EPIC-006 memory management" || {
    echo -e "${RED}Merge conflict in EPIC-006. Resolve conflicts and run: git merge --continue${NC}"
    exit 1
}

# 5. Run initial tests
echo -e "${YELLOW}Running initial test suite...${NC}"
python -m pytest --tb=short -q || {
    echo -e "${YELLOW}Some tests failed. This is expected. Run 'make test' for full output.${NC}"
}

# 6. Show status
echo -e "${GREEN}=== v1.1 Branch Creation Complete ===${NC}"
echo "Current branch: $(git branch --show-current)"
echo "Commits merged: $(git log --oneline develop..HEAD | wc -l)"
echo ""
echo "Next steps:"
echo "1. Run 'make test' to see all test failures"
echo "2. Check 'git status' for any unresolved conflicts"
echo "3. Run 'make deps' to update dependencies"
echo "4. Start fixing integration issues!"
echo ""
echo -e "${GREEN}Good luck with v1.1 integration!${NC}"