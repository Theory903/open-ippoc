#!/usr/bin/env python3
"""
Log Monitoring Service for Open Cortex
Continuously monitors log directory for new files and maintains log health
"""

import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import threading
from dataclasses import asdict

from enhanced_log_manager import EnhancedLogManager


class LogMonitorService:
    """Continuous log monitoring service"""
    
    def __init__(self, base_path: str = "/Users/abhishekjha/CODE/ippoc/src/kernel/openclaw", 
                 check_interval: int = 300):  # 5 minutes
        self.manager = EnhancedLogManager(base_path)
        self.check_interval = check_interval
        self.running = False
        self.last_check = None
        self.stats = {
            "checks_performed": 0,
            "files_processed": 0,
            "errors_detected": 0,
            "maintenance_runs": 0
        }
        
    def start_monitoring(self):
        """Start the monitoring service"""
        print("🚀 Starting Log Monitor Service...")
        print(f"📅 Check interval: {self.check_interval} seconds")
        print(f"📂 Monitoring: {self.manager.base_path}")
        print("Press Ctrl+C to stop\n")
        
        self.running = True
        self._monitoring_loop()
        
    def stop_monitoring(self):
        """Stop the monitoring service"""
        print("\n🛑 Stopping Log Monitor Service...")
        self.running = False
        
    def _monitoring_loop(self):
        """Main monitoring loop"""
        try:
            while self.running:
                self._perform_check()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.stop_monitoring()
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            self.stop_monitoring()
            
    def _perform_check(self):
        """Perform a single monitoring check"""
        try:
            timestamp = datetime.now().isoformat()
            print(f"[{timestamp}] 🔍 Performing log check...")
            
            # Check for new logs
            new_count = self.manager.process_new_logs()
            if new_count > 0:
                print(f"  ✅ Processed {new_count} new log files")
                self.stats["files_processed"] += new_count
            
            # Update stats
            self.stats["checks_performed"] += 1
            self.last_check = timestamp
            
            # Perform maintenance every 6 checks (30 minutes)
            if self.stats["checks_performed"] % 6 == 0:
                self._perform_maintenance()
                
            # Check health metrics occasionally
            if self.stats["checks_performed"] % 12 == 0:  # Every hour
                self._check_health()
                
        except Exception as e:
            print(f"  ❌ Check failed: {e}")
            self.stats["errors_detected"] += 1
            
    def _perform_maintenance(self):
        """Perform routine maintenance"""
        try:
            print("  🔧 Running maintenance...")
            report = self.manager.generate_maintenance_report()
            self.stats["maintenance_runs"] += 1
            
            # Log maintenance results
            maintenance_log = self.manager.organized_path / "maintenance_log.jsonl"
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "files_processed": report.files_processed,
                "duplicates_removed": report.duplicates_removed,
                "files_archived": report.files_archived,
                "space_saved_mb": report.space_saved_mb
            }
            
            with open(maintenance_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
            print(f"    Processed: {report.files_processed} files")
            print(f"    Cleaned: {report.duplicates_removed} duplicates")
            print(f"    Archived: {report.files_archived} files")
            print(f"    Space saved: {report.space_saved_mb:.2f} MB")
            
        except Exception as e:
            print(f"    ❌ Maintenance failed: {e}")
            
    def _check_health(self):
        """Check log system health"""
        try:
            print("  📊 Checking system health...")
            health = self.manager.get_health_metrics()
            
            # Alert on high error rates
            if health.error_rate > 10:
                print(f"    ⚠️  HIGH ERROR RATE: {health.error_rate:.2f}%")
            
            # Alert on large files
            if health.largest_file_mb > 20:
                print(f"    ⚠️  LARGE LOG FILES: {health.largest_file_mb:.2f}MB")
                
            # Save health snapshot
            health_file = self.manager.organized_path / f"health_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(health_file, 'w') as f:
                json.dump(asdict(health), f, indent=2, default=str)
                
        except Exception as e:
            print(f"    ❌ Health check failed: {e}")
    
    def get_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            "running": self.running,
            "last_check": self.last_check,
            "stats": self.stats,
            "uptime": str(datetime.now() - datetime.fromisoformat(self.last_check)) if self.last_check else "N/A"
        }
    
    def generate_report(self) -> Dict:
        """Generate comprehensive monitoring report"""
        try:
            health = self.manager.get_health_metrics()
            status = self.get_status()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "service_status": status,
                "log_health": asdict(health),
                "recommendations": [
                    "Run maintenance weekly to keep logs organized",
                    "Monitor error rates above 5% for potential issues",
                    "Consider log rotation for files > 10MB",
                    "Review provider distribution for load balancing"
                ]
            }
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }


def run_interactive_monitor():
    """Run interactive monitoring session"""
    print("🔍 Open Cortex Log Monitor - Interactive Mode")
    print("=" * 50)
    
    monitor = LogMonitorService()
    
    # Quick health check
    print("\n📊 Initial Health Check:")
    try:
        health = monitor.manager.get_health_metrics()
        print(f"  Files: {health.total_files}")
        print(f"  Entries: {health.total_entries:,}")
        print(f"  Error Rate: {health.error_rate:.2f}%")
        print(f"  Providers: {len(health.file_count_by_provider)} active")
    except Exception as e:
        print(f"  ❌ Health check failed: {e}")
        return
    
    # Menu
    while True:
        print("\n📋 Options:")
        print("1. Process new logs")
        print("2. Run maintenance")
        print("3. Check health")
        print("4. View status")
        print("5. Generate full report")
        print("6. Start continuous monitoring")
        print("7. Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == '1':
            count = monitor.manager.process_new_logs()
            print(f"✅ Processed {count} new files")
            
        elif choice == '2':
            print("🔧 Running maintenance...")
            report = monitor.manager.generate_maintenance_report()
            print(f"  Files: {report.files_processed}")
            print(f"  Duplicates removed: {report.duplicates_removed}")
            print(f"  Space saved: {report.space_saved_mb:.2f} MB")
            
        elif choice == '3':
            try:
                health = monitor.manager.get_health_metrics()
                print(f"\n📊 Health Metrics:")
                print(f"  Total Files: {health.total_files}")
                print(f"  Error Rate: {health.error_rate:.2f}%")
                print(f"  Largest File: {health.largest_file_mb:.2f} MB")
                print(f"  Providers: {', '.join(health.file_count_by_provider.keys())}")
                if health.recommendations:
                    print(f"  Recommendations: {', '.join(health.recommendations)}")
            except Exception as e:
                print(f"❌ Health check failed: {e}")
                
        elif choice == '4':
            status = monitor.get_status()
            print(f"\n📈 Service Status:")
            print(f"  Running: {status['running']}")
            print(f"  Last Check: {status['last_check']}")
            print(f"  Checks Performed: {status['stats']['checks_performed']}")
            
        elif choice == '5':
            report = monitor.generate_report()
            report_file = monitor.manager.organized_path / f"detailed_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"✅ Report saved to {report_file}")
            
        elif choice == '6':
            print("\n🚀 Starting continuous monitoring...")
            print("Press Ctrl+C to return to menu")
            try:
                monitor.start_monitoring()
            except KeyboardInterrupt:
                monitor.stop_monitoring()
                print("\nReturned to menu")
                
        elif choice == '7':
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    run_interactive_monitor()