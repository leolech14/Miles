# 🌿 Miles Repository Branching Strategy

## Overview
We use a **simplified GitHub Flow** with `main` as the single source of truth for maximum simplicity and efficiency.

## Branch Structure

### `main` - Production Branch ✅
- **Purpose**: Production-ready code
- **Protection**: Full CI/CD checks required
- **Deployment**: Auto-deploys to Fly.io on merge
- **History**: Linear (rebase and merge only)

## Development Workflow

### 1. Feature Development
```bash
# Start new feature
git checkout main
git pull origin main
git checkout -b feature/amazing-new-feature

# Work on feature
git add .
git commit -m "feat: add amazing new feature"
git push origin feature/amazing-new-feature
```

### 2. Pull Request Process
```bash
# Create PR: feature/amazing-new-feature → main
# Required checks:
# ✅ pytest (all tests pass)
# ✅ mypy --strict (type checking)
# ✅ ruff check (linting)
# ✅ black --check (formatting)
# ✅ build (Docker image builds)
# ✅ trivy (security scan)
```

### 3. Merge and Deploy
```bash
# After PR approval and checks pass:
# → Rebase and merge to main
# → Automatic deployment to Fly.io
# → Delete feature branch
```

## Branch Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| 🚀 Feature | `feature/description` | `feature/prometheus-metrics` |
| 🐛 Bug Fix | `fix/description` | `fix/rate-limit-error` |
| 🚨 Hotfix | `hotfix/description` | `hotfix/security-patch` |
| 📚 Docs | `docs/description` | `docs/api-documentation` |
| 🧪 Experiment | `experiment/description` | `experiment/new-ai-model` |

## Commit Message Format

```
<type>: <description>

feat: add Prometheus metrics endpoint
fix: resolve rate limiting edge case  
docs: update API documentation
chore: clean up old dependencies
security: patch OpenAI API key validation
```

## Emergency Procedures

### Hotfix Process
```bash
# For critical production issues:
git checkout main
git pull origin main  
git checkout -b hotfix/critical-security-fix

# Make minimal fix
git commit -m "security: patch critical vulnerability"
git push origin hotfix/critical-security-fix

# Create emergency PR with fast-track review
```

### Rollback Process
```bash
# If deployment fails:
git revert <commit-hash>
git push origin main
# This triggers automatic rollback deployment
```

## Why This Strategy?

### ✅ Advantages
- **Simple**: Single branch to track
- **Fast**: Direct path to production
- **Reliable**: All code tested before merge
- **Traceable**: Linear history is easy to follow
- **Automated**: CI/CD handles everything

### 🚫 What We Avoid
- Complex branch hierarchies
- Merge conflicts from long-lived branches
- Manual deployment steps
- Untested code reaching production

## CI/CD Integration

### Automatic Triggers
- **On PR**: Run all tests and checks
- **On merge to main**: Deploy to production
- **On security alert**: Create issue automatically

### Status Checks
All PRs must pass:
1. `pytest` - Test suite
2. `mypy --strict` - Type checking  
3. `ruff check` - Code linting
4. `black --check` - Code formatting
5. `trivy` - Security scanning
6. `build` - Docker image creation

## Best Practices

### For Contributors
- Keep feature branches short-lived (< 1 week)
- Write descriptive commit messages
- Include tests with new features
- Update documentation as needed

### For Reviewers  
- Check code quality and security
- Verify tests cover new functionality
- Ensure documentation is updated
- Test locally if needed

### For Maintainers
- Monitor deployment health
- Review security alerts promptly
- Keep dependencies updated
- Maintain clean commit history

---

**This strategy ensures Miles maintains production quality while enabling rapid, safe iteration.** 🚀
