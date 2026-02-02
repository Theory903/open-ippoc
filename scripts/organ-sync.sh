#!/bin/bash
# IPPOC Organ Synchronization Script
# Pushes organ-specific directories to their own evolution branches.

ORGANS=("brain" "body" "mind" "memory")
REMOTE="origin"

echo "🚀 Starting IPPOC Organ Synchronization..."

for ORGAN in "${ORGANS[@]}"; do
    if [ -d "$ORGAN" ]; then
        echo "📂 Syncing organ: $ORGAN -> evolution/$ORGAN"
        # Check if there are changes to push
        if git subtree push --prefix="$ORGAN" "$REMOTE" "evolution/$ORGAN" 2>/dev/null; then
            echo "✅ Successfully synced $ORGAN"
        else
            echo "⚠️ No changes or error syncing $ORGAN (it might already be up-to-date)"
        fi
    else
        echo "❌ Organ directory $ORGAN not found, skipping."
    fi
done

echo "🏁 Organ synchronization complete."
