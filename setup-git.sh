#!/bin/bash
#
# Quick Git Setup Script for SeenSlide
# Author: Mahmudul Faisal Al Ameen
#

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}  SeenSlide Git Setup${NC}"
echo -e "${BLUE}==================================${NC}"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}Git is not installed. Installing...${NC}"
    sudo apt-get update -qq
    sudo apt-get install -y git
fi

# Check if already initialized
if [ -d ".git" ]; then
    echo -e "${YELLOW}Git repository already initialized${NC}"
    echo -e "${BLUE}Current status:${NC}"
    git status --short
    echo ""
    read -p "Do you want to commit current changes? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        echo "Enter commit message (or press Enter for default):"
        read commit_msg
        if [ -z "$commit_msg" ]; then
            commit_msg="Update SeenSlide codebase"
        fi
        git commit -m "$commit_msg"
        echo -e "${GREEN}Changes committed!${NC}"
    fi
else
    # Configure git
    echo -e "${BLUE}Configuring git...${NC}"
    git config --global user.name "Mahmudul Faisal Al Ameen" 2>/dev/null || true
    git config --global user.email "mahmudulfaisal@gmail.com" 2>/dev/null || true

    # Initialize repository
    echo -e "${BLUE}Initializing repository...${NC}"
    git init
    git branch -M main

    # Add files
    echo -e "${BLUE}Adding files...${NC}"
    git add .

    # Create initial commit
    echo -e "${BLUE}Creating initial commit...${NC}"
    git commit -m "Initial commit: SeenSlide - Real-time Presentation Capture System

- Complete screen capture system with Wayland support
- Admin panel with authentication
- Real-time slide viewer with mobile optimization
- Intelligent deduplication with configurable tolerance
- One-click installer for Ubuntu
- Comprehensive documentation

Developed by Mahmudul Faisal Al Ameen with AI assistance from Claude (Anthropic)"

    echo -e "${GREEN}✓ Repository initialized and files committed${NC}"
fi

echo ""
echo -e "${BLUE}==================================${NC}"
echo -e "${GREEN}Git setup complete!${NC}"
echo -e "${BLUE}==================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "1. Create repository on GitHub:"
echo "   → Go to: https://github.com/new"
echo "   → Name: seenslide"
echo "   → DO NOT initialize with README"
echo ""
echo "2. Push to GitHub:"
echo "   ${BLUE}git remote add origin https://github.com/YOUR_USERNAME/seenslide.git${NC}"
echo "   ${BLUE}git push -u origin main${NC}"
echo ""
echo "Or use GitHub CLI (recommended):"
echo "   ${BLUE}gh repo create seenslide --public --source=. --remote=origin --push${NC}"
echo ""
echo "See GITHUB_SETUP.md for detailed instructions"
echo ""
