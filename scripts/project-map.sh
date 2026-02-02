#!/bin/bash
# IPPOC-OS Project Mapping Utility
# 🧬 Part of the System Evolution Engine

# Default: Respect .gitignore (Show what's relevant)
# --full: Truly ignore .gitignore (Show everything including build artifacts)

MODE="RESPECT"
if [[ "$1" == "--full" ]]; then
    MODE="IGNORE"
fi

echo "--------------------------------------------------------"
if [[ "$MODE" == "IGNORE" ]]; then
    echo "🏗️  MODE: RAW FS (Ignoring .gitignore)"
    echo "⚠️  Warning: This will include bulky build artifacts and dependencies."
    echo "--------------------------------------------------------"
    # Exclude .git directory as it's purely metadata
    tree -a -I '.git'
else
    echo "🧠 MODE: ORGANISM MAP (Respecting .gitignore)"
    echo "💡 This shows only the source code and configuration files."
    echo "--------------------------------------------------------"
    
    # Check if git is available
    if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
        # List tracked + untracked (non-ignored) files and pipe to tree
        # We use git ls-files to get the canonical project list
        git ls-files -co --exclude-standard | tree --fromfile .
    else
        # Fallback if not in a git repo
        tree -I 'node_modules|target|dist|.git|.next|.turbo'
    fi
fi
echo "--------------------------------------------------------"
