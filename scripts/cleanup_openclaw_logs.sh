#!/bin/bash
# OpenClaw Log Cleanup Script
# Runs daily to clean up old log files

# Get the script's directory and resolve LOG_DIR relative to it
# (assuming script stays in <project_root>/scripts/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/src/kernel/openclaw"
ORGANIZED_DIR="$LOG_DIR/organized_logs"
MAX_AGE_DAYS=7

# Clean up old organized logs
find "$ORGANIZED_DIR" -name "*.log" -mtime +$MAX_AGE_DAYS -delete 2>/dev/null

# Compress logs older than 3 days
find "$LOG_DIR" -name "gateway_*.log" -mtime +3 -exec gzip {} \; 2>/dev/null

# Remove logs older than 30 days
find "$LOG_DIR" -name "gateway_*.log*" -mtime +30 -delete 2>/dev/null

echo "$(date): Log cleanup completed" >> /tmp/openclaw_cleanup.log