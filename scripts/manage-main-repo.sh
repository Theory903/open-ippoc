#!/bin/bash

# IPPOC Main Repository Management Script
# Manages the main repository at https://github.com/Theory903/open-ippoc

set -e

REPO_URL="https://github.com/Theory903/open-ippoc.git"
MAIN_BRANCH="main"

show_help() {
    echo "IPPOC Main Repository Manager"
    echo "============================"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  status     - Show repository status and branch info"
    echo "  sync       - Sync with remote repository"
    echo "  push       - Push current changes to main repository"
    echo "  pull       - Pull latest changes from main repository"
    echo "  backup     - Create backup branch before major changes"
    echo "  cleanup    - Clean up old mutation branches"
    echo "  stats      - Show repository statistics"
    echo ""
    echo "Repository: $REPO_URL"
    echo "Main Branch: $MAIN_BRANCH"
}

show_status() {
    echo "=== IPPOC Main Repository Status ==="
    echo "Current branch: $(git branch --show-current)"
    echo "Repository URL: $REPO_URL"
    echo ""
    
    echo "Git status:"
    git status --short
    
    echo ""
    echo "Recent commits:"
    git log --oneline -5
    
    echo ""
    echo "Remote status:"
    git remote -v | grep origin
    
    echo ""
    echo "Branch information:"
    git branch -a | grep -E "(main|feature/|mutation/)" | head -10
}

sync_repo() {
    echo "=== Syncing with Main Repository ==="
    
    # Fetch all remotes
    echo "Fetching from origin..."
    git fetch origin
    
    # Check if we're on main branch
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" != "$MAIN_BRANCH" ]; then
        echo "Switching to $MAIN_BRANCH..."
        git checkout $MAIN_BRANCH
    fi
    
    # Pull latest changes
    echo "Pulling latest changes..."
    git pull origin $MAIN_BRANCH --ff-only
    
    echo "✅ Sync completed successfully"
}

push_changes() {
    echo "=== Pushing Changes to Main Repository ==="
    
    # Check if we're on main branch
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" != "$MAIN_BRANCH" ]; then
        echo "⚠️  Warning: You're not on the main branch ($MAIN_BRANCH)"
        echo "Current branch: $CURRENT_BRANCH"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Operation cancelled"
            exit 1
        fi
    fi
    
    # Check for changes
    if [[ -z $(git status --porcelain) ]]; then
        echo "No changes to push"
        return 0
    fi
    
    # Add all changes
    echo "Adding all changes..."
    git add .
    
    # Show what will be committed
    echo ""
    echo "Changes to be committed:"
    git diff --cached --stat
    
    # Get commit message
    echo ""
    read -p "Enter commit message: " commit_msg
    if [[ -z "$commit_msg" ]]; then
        commit_msg="Update main repository"
    fi
    
    # Commit and push
    echo "Committing changes..."
    git commit -m "$commit_msg"
    
    echo "Pushing to origin..."
    git push origin $MAIN_BRANCH
    
    echo "✅ Changes pushed successfully"
}

pull_changes() {
    echo "=== Pulling Changes from Main Repository ==="
    
    # Check if we're on main branch
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" != "$MAIN_BRANCH" ]; then
        echo "Switching to $MAIN_BRANCH..."
        git checkout $MAIN_BRANCH
    fi
    
    echo "Pulling latest changes..."
    git pull origin $MAIN_BRANCH
    
    echo "✅ Pull completed successfully"
}

create_backup() {
    echo "=== Creating Backup Branch ==="
    
    TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
    BACKUP_BRANCH="backup-$TIMESTAMP"
    
    echo "Creating backup branch: $BACKUP_BRANCH"
    git checkout -b $BACKUP_BRANCH
    
    echo "✅ Backup branch created"
    echo "To return to main: git checkout $MAIN_BRANCH"
}

cleanup_mutations() {
    echo "=== Cleaning Up Mutation Branches ==="
    
    echo "Finding old mutation branches..."
    OLD_MUTATIONS=$(git branch -a | grep "mutation/" | grep -v "\*" | head -10)
    
    if [[ -z "$OLD_MUTATIONS" ]]; then
        echo "No old mutation branches found"
        return 0
    fi
    
    echo "Found mutation branches:"
    echo "$OLD_MUTATIONS"
    echo ""
    
    read -p "Delete these branches? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Deleting mutation branches..."
        echo "$OLD_MUTATIONS" | while read branch; do
            branch_name=$(echo $branch | sed 's/remotes\/origin\///' | xargs)
            if [[ $branch_name == *"remotes/origin/"* ]]; then
                git push origin --delete $branch_name
            else
                git branch -D $branch_name 2>/dev/null || true
            fi
        done
        echo "✅ Cleanup completed"
    else
        echo "Cleanup cancelled"
    fi
}

show_stats() {
    echo "=== Repository Statistics ==="
    
    echo "Total commits: $(git rev-list --count HEAD)"
    echo "Active branches: $(git branch | wc -l)"
    echo "Feature branches: $(git branch | grep "feature/" | wc -l)"
    echo "Mutation branches: $(git branch -a | grep "mutation/" | wc -l)"
    echo ""
    
    echo "Top contributors:"
    git shortlog -sn --all | head -10
    
    echo ""
    echo "Recent activity:"
    git log --since="1 week ago" --oneline | wc -l | xargs echo "Commits in last week:"
}

# Main execution
case "${1:-status}" in
    status)
        show_status
        ;;
    sync)
        sync_repo
        ;;
    push)
        push_changes
        ;;
    pull)
        pull_changes
        ;;
    backup)
        create_backup
        ;;
    cleanup)
        cleanup_mutations
        ;;
    stats)
        show_stats
        ;;
    *)
        show_help
        ;;
esac