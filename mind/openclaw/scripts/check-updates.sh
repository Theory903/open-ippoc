#!/bin/bash

# IPPOC OpenClaw Update Checker
# Checks for available updates from upstream without applying them

echo "=== IPPOC OpenClaw Update Checker ==="

# Fetch upstream changes
git fetch upstream

# Get commit information
UPSTREAM_COMMIT=$(git rev-parse upstream/main)
LOCAL_COMMIT=$(git rev-parse HEAD)

echo "Local commit:  $(git log -1 --oneline HEAD)"
echo "Upstream commit: $(git log -1 --oneline upstream/main)"

if [ "$UPSTREAM_COMMIT" = "$LOCAL_COMMIT" ]; then
    echo "✅ Already up to date with upstream"
    exit 0
fi

echo "🔄 Updates available from upstream"
echo ""

# Show commit differences
if [ "$LOCAL_COMMIT" != "$UPSTREAM_COMMIT" ]; then
    echo "Recent upstream commits:"
    git log --oneline HEAD..upstream/main | head -10
fi

if [ $(git rev-list --count HEAD..upstream/main) -gt 10 ]; then
    echo "... and $(($(git rev-list --count HEAD..upstream/main) - 10)) more commits"
fi

echo ""
echo "To update, run: ./scripts/update-from-upstream.sh"