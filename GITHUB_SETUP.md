# GitHub Repository Setup Guide

Quick guide to create your SeenSlide repository on GitHub and push your code.

## Prerequisites

First, install git if you haven't already:

```bash
sudo apt-get update
sudo apt-get install git
```

Configure git with your information:

```bash
git config --global user.name "Mahmudul Faisal Al Ameen"
git config --global user.email "mahmudulfaisal@gmail.com"
```

## Step 1: Initialize Local Repository

From the SeenSlide directory:

```bash
cd /home/faisal/code/hobby/SeenSlide

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: SeenSlide - Real-time Presentation Capture System

- Complete screen capture system with Wayland support
- Admin panel with authentication
- Real-time slide viewer with mobile optimization
- Intelligent deduplication with configurable tolerance
- One-click installer for Ubuntu
- Comprehensive documentation

Developed by Mahmudul Faisal Al Ameen with AI assistance from Claude (Anthropic)"
```

## Step 2: Create GitHub Repository

### Option A: Using GitHub CLI (Recommended)

Install GitHub CLI:
```bash
sudo apt-get install gh
```

Authenticate:
```bash
gh auth login
# Follow the prompts to authenticate with your GitHub account
```

Create repository and push:
```bash
# Create public repository
gh repo create seenslide --public --source=. --remote=origin --push

# Or create private repository
gh repo create seenslide --private --source=. --remote=origin --push
```

### Option B: Using GitHub Website (Manual)

1. **Go to GitHub**: https://github.com/new

2. **Fill in repository details:**
   - Repository name: `seenslide`
   - Description: `Real-time Presentation Capture & Sharing - Capture slides and share with audience instantly`
   - Visibility: Public (or Private)
   - **Do NOT** initialize with README, .gitignore, or license (we already have these)

3. **Click "Create repository"**

4. **Push your code:**

GitHub will show you commands. Use these:

```bash
git remote add origin https://github.com/YOUR_USERNAME/seenslide.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

## Step 3: Verify Upload

Visit: `https://github.com/YOUR_USERNAME/seenslide`

You should see all your files!

## Step 4: Add Repository Description

On GitHub repository page:

1. Click the gear icon next to "About"
2. Add description: `Real-time Presentation Capture & Sharing Tool`
3. Add topics: `presentation`, `screen-capture`, `slides`, `wayland`, `fastapi`, `python`
4. Add website (if you have one)
5. Save

## Future Updates

After making changes to your code:

```bash
# Check what changed
git status

# Add changes
git add .

# Commit with message
git commit -m "Description of your changes"

# Push to GitHub
git push
```

## Common Git Commands

```bash
# See commit history
git log --oneline

# See what changed
git diff

# Undo changes to a file
git checkout -- filename

# Create a new branch
git checkout -b feature-name

# Switch branches
git checkout main

# Pull latest changes
git pull
```

## Troubleshooting

### Authentication Issues

If you have trouble pushing:

```bash
# Use personal access token instead of password
# Go to: GitHub → Settings → Developer settings → Personal access tokens
# Create token with 'repo' scope
# Use token as password when prompted
```

Or set up SSH keys:
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "mahmudulfaisal@gmail.com"

# Add to ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub
# Add this to GitHub → Settings → SSH and GPG keys

# Change remote to SSH
git remote set-url origin git@github.com:YOUR_USERNAME/seenslide.git
```

### Large Files

If you get errors about large files:

```bash
# Remove file from git (keep local copy)
git rm --cached path/to/large/file

# Add to .gitignore
echo "path/to/large/file" >> .gitignore

# Commit and push
git commit -m "Remove large file"
git push
```

## Next Steps

After pushing to GitHub:

1. **Add README badges** (optional):
   - License badge
   - Python version badge
   - Build status badge

2. **Enable GitHub Pages** (optional):
   - For documentation hosting

3. **Set up GitHub Actions** (optional):
   - Automated testing
   - Automated releases

4. **Create releases**:
   - Tag version: `git tag v1.0.0`
   - Push tags: `git push --tags`
   - Create release on GitHub with installer

---

**Questions?** Check GitHub's official documentation: https://docs.github.com
