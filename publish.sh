#!/bin/bash
#
# Quick commands to finalize and push the repository
# Run these commands to publish your project to GitHub
#

set -e

echo "🚀 Gmail Newsletter Manager - Git Commands for Publishing"
echo "=========================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Update GitHub Username Placeholders${NC}"
echo "Run this command (replace 'yourusername' with your actual GitHub username):"
echo -e "${BLUE}  find . -type f \( -name '*.md' -o -name '*.toml' -o -name '*.yml' \) -not -path './venv/*' -exec sed -i '' 's/YOUR-USERNAME/yourusername/g' {} +${NC}"
echo ""

echo -e "${YELLOW}Step 2: Verify Changes${NC}"
echo "Review what will be committed:"
echo -e "${BLUE}  git status${NC}"
echo -e "${BLUE}  git diff --cached${NC}"
echo ""

echo -e "${YELLOW}Step 3: Run Pre-Push Validation${NC}"
echo "Make sure all checks pass:"
echo -e "${BLUE}  ./pre-push.sh${NC}"
echo ""

echo -e "${YELLOW}Step 4: Create First Commit${NC}"
echo "Commit all the changes:"
echo -e "${BLUE}  git commit -m '🎉 Initial open source release v0.1.0

Intelligent Gmail newsletter management utility built on gogcli

Features:
- Smart newsletter detection with multiple heuristics
- Hierarchical label organization
- Multi-account support
- Gmail Takeout import
- Auto-categorization
- SQLite database storage

Complete with:
- Comprehensive documentation
- CI/CD workflows
- Security policy
- Contributing guidelines
- Example configuration'${NC}"
echo ""

echo -e "${YELLOW}Step 5: Create GitHub Repository${NC}"
echo "1. Go to https://github.com/new"
echo "2. Repository name: gmail-newsletter-manager"
echo "3. Description: 🚀 Intelligent Gmail newsletter management utility built on gogcli"
echo "4. Keep it public"
echo "5. DO NOT initialize with README (we already have one)"
echo "6. Click 'Create repository'"
echo ""

echo -e "${YELLOW}Step 6: Add Remote and Push${NC}"
echo "After creating the GitHub repository, run:"
echo -e "${BLUE}  git remote add origin https://github.com/yourusername/gmail-newsletter-manager.git${NC}"
echo -e "${BLUE}  git branch -M main${NC}"
echo -e "${BLUE}  git push -u origin main${NC}"
echo ""

echo -e "${YELLOW}Step 7: Post-Push Configuration${NC}"
echo "After pushing, configure GitHub repository:"
echo "1. Add topics: gmail, newsletter, email, automation, python, productivity"
echo "2. Enable Issues"
echo "3. Set up branch protection for 'main'"
echo "4. Add repository description"
echo ""

echo -e "${YELLOW}Step 8: Create First Release${NC}"
echo "1. Go to: https://github.com/yourusername/gmail-newsletter-manager/releases/new"
echo "2. Tag version: v0.1.0"
echo "3. Release title: v0.1.0 - Initial Release"
echo "4. Description: Copy from CHANGELOG.md"
echo "5. Publish release"
echo ""

echo -e "${GREEN}✨ That's it! Your project will be live on GitHub!${NC}"
echo ""
