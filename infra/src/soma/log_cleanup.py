#!/usr/bin/env python3
"""
Open Cortex Log Cleanup Script
Removes duplicate and redundant log files to improve log management
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def cleanup_openclaw_logs():
    """Clean up redundant OpenClaw log files"""
    log_dir = Path("/Users/abhishekjha/CODE/ippoc/src/kernel/openclaw")
    
    print("🧹 Open Cortex Log Cleanup")
    print("=" * 35)
    
    # Patterns to identify duplicate/redundant logs
    duplicate_patterns = [
        # Versioned duplicates
        "gateway_groq_v*.log",
        "gateway_ollama_v*.log", 
        "gateway_ippoc_sync_v*.log",
        "gateway_ippoc_fix_v*.log",
        "gateway_fixed_*.log",
        
        # Redundant logs
        "gateway_dev_default.log",
        "gateway_dev_token.log", 
        "gateway_final_token.log",
        "gateway_final.log"
    ]
    
    files_deleted = []
    total_saved_space = 0
    
    for pattern in duplicate_patterns:
        matching_files = list(log_dir.glob(pattern))
        
        if len(matching_files) > 1:
            # Sort by modification time, keep the newest
            matching_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Delete all but the newest
            for file_to_delete in matching_files[1:]:
                try:
                    file_size = file_to_delete.stat().st_size
                    file_to_delete.unlink()
                    files_deleted.append(file_to_delete.name)
                    total_saved_space += file_size
                    print(f"  Deleted: {file_to_delete.name}")
                except Exception as e:
                    print(f"  Failed to delete {file_to_delete.name}: {e}")
    
    print(f"\n✅ Cleanup Complete!")
    print(f"  Files deleted: {len(files_deleted)}")
    print(f"  Space saved: {total_saved_space / 1024:.1f} KB")
    
    # Show remaining log files
    remaining_logs = list(log_dir.glob("gateway_*.log"))
    print(f"  Remaining log files: {len(remaining_logs)}")
    
    return files_deleted

def create_log_rotation_config():
    """Create log rotation configuration"""
    config_content = """
# OpenClaw Gateway Log Rotation Configuration
# Place this in /etc/logrotate.d/openclaw or equivalent

/Users/abhishekjha/CODE/ippoc/src/kernel/openclaw/gateway_*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 abhishekjha staff
    postrotate
        # Restart gateway service if needed
        # systemctl reload openclaw-gateway || true
    endscript
}
"""
    
    config_path = Path("/Users/abhishekjha/CODE/ippoc/openclaw_logrotate.conf")
    with open(config_path, 'w') as f:
        f.write(config_content.strip())
    
    print(f"📝 Log rotation config created: {config_path}")
    return config_path

def setup_log_cleanup_cron():
    """Setup automatic log cleanup cron job"""
    cron_script = """
#!/bin/bash
# OpenClaw Log Cleanup Script
# Runs daily to clean up old log files

LOG_DIR="/Users/abhishekjha/CODE/ippoc/src/kernel/openclaw"
ORGANIZED_DIR="$LOG_DIR/organized_logs"
MAX_AGE_DAYS=7

# Clean up old organized logs
find "$ORGANIZED_DIR" -name "*.log" -mtime +$MAX_AGE_DAYS -delete 2>/dev/null

# Compress logs older than 3 days
find "$LOG_DIR" -name "gateway_*.log" -mtime +3 -exec gzip {} \\; 2>/dev/null

# Remove logs older than 30 days
find "$LOG_DIR" -name "gateway_*.log*" -mtime +30 -delete 2>/dev/null

echo "$(date): Log cleanup completed" >> /tmp/openclaw_cleanup.log
"""
    
    script_path = Path("/Users/abhishekjha/CODE/ippoc/scripts/cleanup_openclaw_logs.sh")
    script_path.parent.mkdir(exist_ok=True)
    
    with open(script_path, 'w') as f:
        f.write(cron_script.strip())
    
    # Make executable
    os.chmod(script_path, 0o755)
    
    print(f"🔧 Cleanup script created: {script_path}")
    return script_path

def main():
    """Run the complete log cleanup and setup"""
    print("🚀 Open Cortex Log Management Setup")
    print("=" * 45)
    
    # Run cleanup
    deleted_files = cleanup_openclaw_logs()
    
    # Create rotation config
    config_path = create_log_rotation_config()
    
    # Setup cleanup script
    script_path = setup_log_cleanup_cron()
    
    print(f"\n✅ Log Management Setup Complete!")
    print(f"  • {len(deleted_files)} duplicate files removed")
    print(f"  • Log rotation config: {config_path}")
    print(f"  • Cleanup script: {script_path}")
    print(f"  • Organized logs: /Users/abhishekjha/CODE/ippoc/src/kernel/openclaw/organized_logs/")

if __name__ == "__main__":
    main()
