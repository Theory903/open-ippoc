#!/bin/bash

# IPPOC Main Repository Management Script
# Manages the main repository at https://github.com/Theory903/open-ippoc

set -e

echo "=== IPPOC Main Repository Manager ==="
echo "Repository: https://github.com/Theory903/open-ippoc"
echo ""

# Function to show current status
show_status() {
    echo "Current branch: $(git branch --show-current)"
    echo "Remote 'origin': $(git remote get-url origin)"
    echo ""
    
    # Show uncommitted changes
    if [[ -n "$(git status --porcelain)" ]]; then
        echo "Uncommitted changes:"
        git status --short
        echo ""
    fi
    
    # Show recent commits
    echo "Recent commits on current branch:"
    git log --oneline -5
    echo ""
}

# Function to sync with main branch
sync_with_main() {
    echo "Syncing with main branch..."
    
    # Fetch latest changes
    git fetch origin
    
    # Check if we're already on main
    if [[ "$(git branch --show-current)" != "main" ]]; then
        echo "Switching to main branch..."
        git checkout main
    fi
    
    # Pull latest changes
    echo "Pulling latest changes from origin/main..."
    git pull origin main --ff-only
    
    echo "✅ Synced with main branch"
}

# Function to create/update main from current work
update_main_from_current() {
    local current_branch=$(git branch --show-current)
    
    echo "Updating main branch from $current_branch..."
    
    # Stash any uncommitted changes
    if [[ -n "$(git status --porcelain)" ]]; then
        echo "Stashing uncommitted changes..."
        git stash push -m "Auto-stash before main update"
        local stashed=true
    fi
    
    # Switch to main
    git checkout main
    
    # Merge current branch into main
    echo "Merging $current_branch into main..."
    git merge --no-ff "$current_branch" -m "Merge $current_branch into main"
    
    # Push to origin
    echo "Pushing to origin/main..."
    git push origin main
    
    # Return to original branch
    git checkout "$current_branch"
    
    # Restore stashed changes if any
    if [[ "$stashed" == "true" ]]; then
        echo "Restoring stashed changes..."
        git stash pop
    fi
    
    echo "✅ Main branch updated successfully"
}

# Function to push current branch to origin
push_current_branch() {
    local current_branch=$(git branch --show-current)
    
    echo "Pushing $current_branch to origin..."
    
    # Set upstream if not already set
    if ! git rev-parse --abbrev-ref "$current_branch@{upstream}" >/dev/null 2>&1; then
        git push -u origin "$current_branch"
    else
        git push origin "$current_branch"
    fi
    
    echo "✅ Pushed $current_branch to origin"
}

# Main command processing
case "${1:-help}" in
    status)
        show_status
        ;;
    sync)
        sync_with_main
        ;;
    update-main)
        update_main_from_current
        ;;
    push)
        push_current_branch
        ;;
    help|*)
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  status      - Show current repository status"
        echo "  sync        - Sync main branch with origin"
        echo "  update-main - Update main branch from current branch"
        echo "  push        - Push current branch to origin"
        echo "  help        - Show this help message"
        echo ""
        echo "Repository: https://github.com/Theory903/open-ippoc"
        ;;
esac