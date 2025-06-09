# Miles Repository Branch Strategy

## Simple Main-Based Workflow

We use a **simplified GitHub Flow** with `main` as the single source of truth:

### Branch Protection Rules for `main`:
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging
  - ✅ CI (pytest, mypy, ruff)  
  - ✅ Build
- ✅ Require branches to be up to date before merging
- ✅ Require linear history (rebase and merge)
- ❌ Include administrators (for flexibility)
- ❌ Allow force pushes
- ❌ Allow deletions

## Workflow

```
feature/new-feature → main (production)
         ↓             ↓
       PR #1       Auto-deploy
```

### Development Process:
1. **Feature Development**: Create `feature/*` branches from `main`
2. **Pull Request**: `feature/*` → `main` 
3. **Auto-Deploy**: Merging to `main` triggers Fly.io deployment
4. **Hotfixes**: `hotfix/*` → `main` (for urgent fixes)

## Auto-merge Rules

- ✅ Allow auto-merge for dependency updates (Dependabot)
- ✅ Allow auto-merge for CI fixes with passing tests
- ❌ Block auto-merge for security changes
