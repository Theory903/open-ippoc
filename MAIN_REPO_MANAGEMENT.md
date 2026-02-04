# IPPOC Main Repository Management

This document explains how to maintain your main repository at https://github.com/Theory903/open-ippoc

## Repository Structure

- **Origin**: `https://github.com/Theory903/open-ippoc.git` (your main repository)
- **Main Branch**: `main` (stable branch for production code)
- **Feature Branches**: Various `feature/*` and `ippoc/mutation/*` branches for development
- **Working Directory**: `/Users/abhishekjha/CODE/ippoc`

## Management Script

Use the `manage_main_repo.sh` script for common repository operations:

```bash
# Check current status
./manage_main_repo.sh status

# Sync main branch with origin
./manage_main_repo.sh sync

# Update main branch from current branch
./manage_main_repo.sh update-main

# Push current branch to origin
./manage_main_repo.sh push
```

## Workflow Recommendations

### Daily Development Workflow

1. **Start work on a feature branch**:
   ```bash
   git checkout -b feature/new-feature
   # Make your changes
   ```

2. **Commit regularly**:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. **Push your feature branch**:
   ```bash
   ./manage_main_repo.sh push
   ```

### Integrating Changes to Main

When your feature is ready:

1. **Update main branch**:
   ```bash
   ./manage_main_repo.sh update-main
   ```

2. **Or manually merge**:
   ```bash
   git checkout main
   git merge feature/new-feature
   git push origin main
   ```

### Keeping Your Repository Clean

1. **Regular cleanup**:
   ```bash
   git remote prune origin  # Remove stale remote branches
   git gc                   # Optimize repository
   ```

2. **Delete merged branches**:
   ```bash
   git branch --merged | grep -v "\*\|main" | xargs -n 1 git branch -d
   ```

## Branch Naming Conventions

- `main` - Production/stable code
- `feature/*` - New features in development  
- `ippoc/mutation/*` - Experimental changes and mutations
- `hotfix/*` - Urgent production fixes
- `release/*` - Release preparation branches

## Best Practices

1. **Always sync main before starting new work**:
   ```bash
   ./manage_main_repo.sh sync
   ```

2. **Use descriptive commit messages**:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `refactor:` for code refactoring
   - `test:` for adding tests

3. **Keep commits atomic** - One logical change per commit

4. **Regular backups** - The script automatically stashes changes when needed

## Troubleshooting

### If you get merge conflicts:
```bash
git status  # See conflicting files
# Resolve conflicts manually
git add .
git commit
```

### If you need to undo changes:
```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit and changes
git reset --hard HEAD~1
```

### If origin rejects pushes:
```bash
git fetch origin
git rebase origin/main
# Resolve any conflicts
git push origin your-branch
```

## Repository Health Checks

Regular commands to run:

```bash
# Check repository size
du -sh .git

# Check for large files
git rev-list --objects --all | grep "$(git verify-pack -v .git/objects/pack/*.idx | sort -k 3 -n | cut -f 1 -d " " | tail -10)"

# Check branch status
git branch -v
```

Your main repository at https://github.com/Theory903/open-ippoc is now properly maintained with automated tools and clear workflows.