# Git Workflow Quick Reference

## 🚀 Starting a New Feature

```bash
# 1. Make sure main is up to date
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/feature-name

# 3. Update README.md to mark feature as "In Progress"
# Edit README.md: Add to "🔄 IN PROGRESS" section

# 4. Commit the plan
git add README.md
git commit -m "Plan: Add [feature name]"
git push origin feature/feature-name
```

## 💻 Working on Feature

```bash
# Make changes, test, commit frequently
git add .
git commit -m "Implement: [what you did]"

# Push to remote (backup and collaboration)
git push origin feature/feature-name
```

## ✅ Completing a Feature

```bash
# 1. Test thoroughly
python3 test_all.py
# Manual testing
# Edge cases

# 2. Update README.md
# - Move feature from "In Progress" to "What Works"
# - Update "Last Updated" date
# - Add usage instructions if needed

# 3. Commit documentation
git add README.md
git commit -m "Docs: Complete [feature name] documentation"

# 4. Merge to main
git checkout main
git pull origin main  # Get latest changes
git merge feature/feature-name

# 5. Test on main branch
python3 test_all.py

# 6. Push to remote
git push origin main

# 7. Delete feature branch
git branch -d feature/feature-name
git push origin --delete feature/feature-name
```

## 🔄 Current Branch Status

```bash
# Check current branch
git branch

# See all branches
git branch -a

# Switch branches
git checkout branch-name
```

## 📝 Commit Message Templates

```bash
# Planning
git commit -m "Plan: Add order parsing feature"

# Implementation
git commit -m "Implement: Basic order parsing logic"
git commit -m "Implement: Menu item matching algorithm"

# Bug fixes
git commit -m "Fix: Handle empty transcription gracefully"

# Documentation
git commit -m "Docs: Update README with order parsing usage"

# Testing
git commit -m "Test: Add order parsing test cases"

# Refactoring
git commit -m "Refactor: Extract order parsing to separate function"
```

## 🎯 README.md Update Template

When starting a feature:
```markdown
### What's In Progress
- 🔄 Order parsing (feature/order-parsing branch)
```

When completing a feature:
```markdown
### What Works
- ✅ Order parsing from conversation
```

## 🚨 Emergency: Need to Switch Features

```bash
# Save current work
git add .
git commit -m "WIP: Saving progress on [feature]"
git push origin feature/current-feature

# Switch to other work
git checkout main
git checkout -b feature/urgent-feature

# Later, come back
git checkout feature/current-feature
# Continue where you left off
```

## 📊 Checking Status

```bash
# What changed?
git status

# What's different from main?
git diff main

# Commit history
git log --oneline

# See all branches with last commit
git branch -v
```

## 🔍 Before Merging Checklist

- [ ] All tests pass (`python3 test_all.py`)
- [ ] Feature works as expected
- [ ] README.md updated
- [ ] No debug code left in
- [ ] Commit messages are clear
- [ ] No conflicts with main

## 💡 Best Practices

1. **Commit often** - Small, focused commits
2. **Push regularly** - Backup your work
3. **Test before merging** - Main should always work
4. **Update README.md** - Keep docs in sync
5. **Delete merged branches** - Keep repo clean

## 🎓 Example: Complete Feature Workflow

```bash
# Start
git checkout main
git checkout -b feature/order-parsing

# Plan
# Edit README.md
git add README.md
git commit -m "Plan: Add order parsing feature"

# Implement
# Write code
git add streaming_voice_agent.py
git commit -m "Implement: Basic order parsing"

# More implementation
# Write more code
git add streaming_voice_agent.py
git commit -m "Implement: Menu item matching"

# Test and fix
# Fix bugs
git add streaming_voice_agent.py
git commit -m "Fix: Handle special characters in menu items"

# Document
# Update README.md
git add README.md
git commit -m "Docs: Add order parsing usage guide"

# Merge
git checkout main
git merge feature/order-parsing
python3 test_all.py  # Verify
git push origin main

# Cleanup
git branch -d feature/order-parsing
```

---

**Remember**:
- Work on feature branches
- Keep main stable
- Update README.md
- Test before merging
