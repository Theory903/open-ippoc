#!/bin/bash

# IPPOC OpenClaw Update Script
# Fetches updates from upstream openclaw/openclaw and merges them into the IPPOC fork

set -e

echo "=== IPPOC OpenClaw Updater ==="
echo "Fetching updates from upstream..."

# Fetch all remotes
git fetch --all

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Fetch upstream changes
git fetch upstream

# Check if there are upstream changes
UPSTREAM_COMMIT=$(git rev-parse upstream/main)
LOCAL_COMMIT=$(git rev-parse HEAD)

if [ "$UPSTREAM_COMMIT" = "$LOCAL_COMMIT" ]; then
    echo "Already up to date with upstream"
    exit 0
fi

echo "Updates available from upstream"
echo "Upstream commit: $UPSTREAM_COMMIT"
echo "Local commit: $LOCAL_COMMIT"

# Create backup branch
BACKUP_BRANCH="backup-before-update-$(date +%Y%m%d-%H%M%S)"
git branch "$BACKUP_BRANCH"
echo "Created backup branch: $BACKUP_BRANCH"

# Attempt to merge upstream changes
echo "Merging upstream changes..."
if git merge upstream/main --no-edit --allow-unrelated-histories; then
    echo "Merge successful!"
    
    # Run build to test compatibility
    echo "Building to test compatibility..."
    if pnpm build; then
        echo "Build successful - IPPOC fork is compatible with upstream changes"
    else
        echo "Build failed - reverting changes"
        git reset --hard "$LOCAL_COMMIT"
        git branch -D "$BACKUP_BRANCH"
        exit 1
    fi
    
else
    echo "Merge conflicts detected - manual resolution required"
    echo "Backup branch created: $BACKUP_BRANCH"
    echo "Resolve conflicts and then run 'pnpm build' to test"
    exit 1
fi

echo "=== Update Complete ==="
echo "Branch: $CURRENT_BRANCH"
echo "Backup branch: $BACKUP_BRANCH (keep until verified stable)"