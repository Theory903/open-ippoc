#!/bin/bash

# Script to generate filesystem structure for openclaw subdirectories
# Usage: ./generate_openclaw_fs.sh [output_file]
#        ./generate_openclaw_fs.sh --clean  (to remove test files, node_modules, and packages)

set -eo pipefail
shopt -s nullglob

OPENCLAW_DIR="/Users/abhishekjha/CODE/ippoc/src/kernel/openclaw"
TARGET_DIRS=("extensions" "docs" "git-hooks" "skills" "src")

# Default output file
OUTPUT_FILE="openclaw_filesystem.txt"

# Check for clean flag
CLEAN_MODE=false
OUTPUT_FILE="openclaw_filesystem.txt"

if [[ $# -gt 0 ]]; then
    if [[ "$1" == "--clean" ]]; then
        CLEAN_MODE=true
    else
        OUTPUT_FILE="$1"
    fi
fi

# Validate openclaw directory exists
if [[ ! -d "$OPENCLAW_DIR" ]]; then
    echo "Error: OpenClaw directory not found at $OPENCLAW_DIR" >&2
    exit 1
fi

# Clean mode function
clean_openclaw() {
    echo "Starting cleanup of OpenClaw directory..."
    
    # Remove all test files (files ending with .test.ts, .test.js, test.ts, test.js)
    echo "Removing test files..."
    find "$OPENCLAW_DIR" -type f \( -name "*.test.ts" -o -name "*.test.js" -o -name "test.ts" -o -name "test.js" \) -delete
    echo "Test files removed successfully."
    
    # Remove all node_modules directories
    echo "Removing node_modules directories..."
    find "$OPENCLAW_DIR" -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
    echo "node_modules directories removed successfully."
    
    # Remove all packages directories
    echo "Removing packages directories..."
    find "$OPENCLAW_DIR" -type d -name "packages" -exec rm -rf {} + 2>/dev/null || true
    echo "packages directories removed successfully."
    
    echo "Cleanup completed!"
    exit 0
}

# Execute clean mode if requested
if [[ "$CLEAN_MODE" == true ]]; then
    clean_openclaw
fi

# Function to generate tree structure
generate_tree() {
    local dir="$1"
    local prefix="$2"
    
    # Get sorted list of items (files and directories)
    local items=()
    while IFS= read -r -d '' item; do
        items+=("$item")
    done < <(find "$dir" -maxdepth 1 -mindepth 1 -print0 | sort -z)
    
    # Handle empty directories
    if [[ ${#items[@]} -eq 0 ]]; then
        return
    fi
    
    local count=${#items[@]}
    local index=0
    
    for item in "${items[@]}"; do
        index=$((index + 1))
        local basename=$(basename "$item")
        local is_last=$((index == count ? 1 : 0))
        
        # Determine prefix for this item
        if [[ $is_last -eq 1 ]]; then
            echo "${prefix}└── ${basename}"
            local new_prefix="${prefix}    "
        else
            echo "${prefix}├── ${basename}"
            local new_prefix="${prefix}│   "
        fi
        
        # Recursively process directories
        if [[ -d "$item" ]]; then
            generate_tree "$item" "$new_prefix"
        fi
    done
}

# Main execution
{
    echo "OpenClaw Filesystem Structure"
    echo "============================="
    echo "Generated on: $(date)"
    echo ""
    
    for dir_name in "${TARGET_DIRS[@]}"; do
        full_path="${OPENCLAW_DIR}/${dir_name}"
        
        if [[ -d "$full_path" ]]; then
            echo "${dir_name}/"
            generate_tree "$full_path" ""
            echo ""
        else
            echo "Warning: Directory $dir_name not found" >&2
        fi
    done
} > "$OUTPUT_FILE"

echo "Filesystem structure written to: $OUTPUT_FILE"