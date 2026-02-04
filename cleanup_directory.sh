#!/bin/bash

# IPPOC Directory Cleanup Script
# Removes unused files and makes the directory structure more professional

echo "🚀 Starting IPPOC directory cleanup..."

# Store current directory
ORIGINAL_DIR=$(pwd)

# Navigate to project root
cd /Users/abhishekjha/CODE/ippoc

echo "🧹 Removing log files..."
find . -name "*.log" -type f -not -path "./logs/*" -delete
echo "✅ Log files removed"

echo "🧹 Removing .DS_Store files..."
find . -name ".DS_Store" -type f -delete
echo "✅ .DS_Store files removed"

echo "🧹 Removing Python cache directories..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
echo "✅ Python cache directories removed"

echo "🧹 Removing pytest cache..."
rm -rf .pytest_cache 2>/dev/null
echo "✅ pytest cache removed"

echo "🧹 Removing target directory (Rust build artifacts)..."
rm -rf target 2>/dev/null
echo "✅ Target directory removed"

echo "🧹 Removing backup files..."
find . -name "*.bak" -type f -delete
echo "✅ Backup files removed"

echo "🧹 Cleaning up documentation files..."
# Remove redundant documentation files that were created during optimization
rm -f IPPOC_INTEGRATED_FLOW.md 2>/dev/null
rm -f IPPOC_DOCUMENTATION_MAP.md 2>/dev/null
rm -f PERFORMANCE_OPTIMIZATION_SUMMARY.md 2>/dev/null
rm -f OPTIMIZATION_COMPLETION_REPORT.md 2>/dev/null
echo "✅ Documentation cleanup completed"

echo "🧹 Removing temporary files..."
find . -name "*.tmp" -type f -delete 2>/dev/null
find . -name "*.temp" -type f -delete 2>/dev/null
echo "✅ Temporary files removed"

echo "🧹 Cleaning up node_modules in extensions (they should use root node_modules)..."
find ./mind/openclaw/extensions -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null
find ./mind/openclaw/packages -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null
find ./brain/cortex -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null
echo "✅ Extension node_modules cleaned"

echo "🧹 Removing unused build directories..."
find . -name "dist" -type d -path "*/node_modules/*" -prune -o -name "dist" -type d -exec rm -rf {} + 2>/dev/null
find . -name "build" -type d -path "*/node_modules/*" -prune -o -name "build" -type d -exec rm -rf {} + 2>/dev/null
echo "✅ Build directories cleaned"

echo "🧹 Cleaning up debug files in TUI..."
rm -f ./mind/tui/*.log 2>/dev/null
echo "✅ TUI debug files removed"

echo "🧹 Removing body.log file..."
rm -f body.log 2>/dev/null
echo "✅ body.log removed"

echo "🧹 Cleaning up virtual environment cache..."
find .venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
echo "✅ Virtual environment cache cleaned"

echo ""
echo "✨ Directory cleanup completed!"
echo ""
echo "📁 Current directory size:"
du -sh . 2>/dev/null | cut -f1
echo ""
echo "📦 Major directories:"
du -sh */ 2>/dev/null | head -10

# Return to original directory
cd "$ORIGINAL_DIR"