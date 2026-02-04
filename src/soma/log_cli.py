#!/usr/bin/env python3
"""
Open Cortex Log Manager CLI
Command-line interface for log management operations
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from enhanced_log_manager import EnhancedLogManager
from log_monitor_service import LogMonitorService


def main():
    parser = argparse.ArgumentParser(description="Open Cortex Log Manager")
    parser.add_argument('--path', default="/Users/abhishekjha/CODE/ippoc/src/kernel/openclaw",
                       help="Base path for log files")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Health check command
    subparsers.add_parser('health', help='Check log system health')
    
    # Process new logs command
    subparsers.add_parser('process', help='Process new log files')
    
    # Maintenance command
    maintenance_parser = subparsers.add_parser('maintain', help='Run maintenance operations')
    maintenance_parser.add_argument('--archive-days', type=int, default=30,
                                  help='Archive logs older than N days')
    maintenance_parser.add_argument('--compress-threshold', type=float, default=5.0,
                                  help='Compress files larger than N MB')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Start monitoring service')
    monitor_parser.add_argument('--interval', type=int, default=300,
                              help='Check interval in seconds')
    
    # Report command
    subparsers.add_parser('report', help='Generate comprehensive report')
    
    # Dashboard command
    subparsers.add_parser('dashboard', help='Create dashboard summary')
    
    # Cleanup command
    subparsers.add_parser('cleanup', help='Clean duplicate files')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize manager
    manager = EnhancedLogManager(args.path)
    
    try:
        if args.command == 'health':
            print("📊 Log System Health Check")
            print("=" * 30)
            health = manager.get_health_metrics()
            print(f"Total Files: {health.total_files}")
            print(f"Total Entries: {health.total_entries:,}")
            print(f"Error Rate: {health.error_rate:.2f}%")
            print(f"Largest File: {health.largest_file_mb:.2f} MB")
            print(f"Date Range: {health.oldest_entry} to {health.newest_entry}")
            print(f"Providers: {', '.join(health.file_count_by_provider.keys())}")
            
            if health.recommendations:
                print("\n💡 Recommendations:")
                for rec in health.recommendations:
                    print(f"  • {rec}")
                    
        elif args.command == 'process':
            print("🔍 Processing new log files...")
            count = manager.process_new_logs()
            print(f"✅ Processed {count} new files")
            
        elif args.command == 'maintain':
            print("🔧 Running maintenance operations...")
            # Clean duplicates
            dup_count, space_saved = manager.clean_duplicate_logs()
            print(f"Duplicates removed: {dup_count} ({space_saved:.2f} MB saved)")
            
            # Archive old logs
            archived = manager.archive_old_logs(days_old=args.archive_days)
            print(f"Archived {archived} old files")
            
            # Compress large files
            compressed = manager.compress_large_logs(size_threshold=args.compress_threshold)
            print(f"Compressed {compressed} large files")
            
            # Generate report
            report = manager.generate_maintenance_report()
            report_file = manager.organized_path / f"cli_maintenance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report.__dict__, f, indent=2, default=str)
            print(f"✅ Maintenance report saved to {report_file}")
            
        elif args.command == 'monitor':
            print("🚀 Starting Log Monitor Service...")
            print(f"Interval: {args.interval} seconds")
            monitor = LogMonitorService(args.path, args.interval)
            monitor.start_monitoring()
            
        elif args.command == 'report':
            print("📋 Generating comprehensive report...")
            manager = EnhancedLogManager(args.path)
            # Process any new logs first
            new_count = manager.process_new_logs()
            if new_count > 0:
                print(f"Processed {new_count} new files")
            
            # Generate maintenance report
            report = manager.generate_maintenance_report()
            report_file = manager.organized_path / f"full_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report.__dict__, f, indent=2, default=str)
            print(f"✅ Full report saved to {report_file}")
            
        elif args.command == 'dashboard':
            print("📊 Creating dashboard summary...")
            summary = manager.create_dashboard_summary()
            summary_file = manager.organized_path / "dashboard_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"✅ Dashboard summary saved to {summary_file}")
            
        elif args.command == 'cleanup':
            print("🧹 Cleaning duplicate files...")
            count, space_saved = manager.clean_duplicate_logs()
            print(f"Removed {count} duplicate files")
            print(f"Space saved: {space_saved:.2f} MB")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    exit(main())