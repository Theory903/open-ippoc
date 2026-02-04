#!/usr/bin/env python3
"""
Enhanced Log Manager for Open Cortex
Provides advanced log monitoring, analysis, and automated maintenance
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import shutil
import hashlib
from collections import defaultdict, Counter
import re

from log_manager import OpenCortexLogManager, LogEntry

# Define log categories locally
LogCategory = {
    'AUTHENTICATION': 'authentication',
    'CONNECTION': 'connection',
    'SYSTEM': 'system',
    'ERROR': 'error',
    'BROWSER': 'browser',
    'AGENT': 'agent',
    'NODE': 'node',
    'CHAT': 'chat',
    'CONFIG': 'config',
    'DIAGNOSTIC': 'diagnostic'
}


@dataclass
class LogHealthMetrics:
    """Metrics for log system health"""
    total_files: int
    total_entries: int
    error_rate: float
    avg_entries_per_file: float
    largest_file_mb: float
    oldest_entry: str
    newest_entry: str
    file_count_by_provider: Dict[str, int]
    error_patterns: List[tuple]
    recommendations: List[str]


@dataclass
class LogMaintenanceReport:
    """Report from log maintenance operations"""
    timestamp: str
    files_processed: int
    duplicates_removed: int
    files_archived: int
    space_saved_mb: float
    health_metrics: LogHealthMetrics


class EnhancedLogManager:
    """Enhanced log management with monitoring and maintenance capabilities"""
    
    def __init__(self, base_path: str = "/Users/abhishekjha/CODE/ippoc/src/kernel/openclaw"):
        self.base_path = Path(base_path)
        self.organized_path = self.base_path / "organized_logs"
        self.log_manager = OpenCortexLogManager(str(self.base_path))
        self.providers = ['ollama', 'ippoc', 'groq', 'kimi', 'fixed', 'dev', 'final']
        
    def scan_for_new_logs(self) -> List[Path]:
        """Scan for new log files that haven't been processed yet"""
        existing_files = set()
        if self.organized_path.exists():
            for log_file in self.organized_path.rglob("*.log"):
                existing_files.add(log_file.name)
        
        new_logs = []
        for log_file in self.base_path.glob("gateway_*.log"):
            if log_file.name not in existing_files:
                new_logs.append(log_file)
                
        return new_logs
    
    def process_new_logs(self) -> int:
        """Process any new log files found"""
        new_logs = self.scan_for_new_logs()
        processed_count = 0
        
        for log_file in new_logs:
            print(f"Processing new log: {log_file.name}")
            try:
                # Copy to organized structure
                entries = self.log_manager.parse_log_file(log_file)
                if entries:
                    # Determine category and organize
                    self._organize_single_file(log_file, entries)
                    processed_count += 1
            except Exception as e:
                print(f"Error processing {log_file.name}: {e}")
                
        return processed_count
    
    def _organize_single_file(self, log_file: Path, entries: List[LogEntry]):
        """Organize a single log file into the proper structure"""
        # Determine provider/category
        filename = log_file.name.lower()
        category = "other"
        
        for provider in self.providers:
            if provider in filename:
                if provider == 'ollama':
                    category = 'ollama_provider'
                elif provider == 'ippoc':
                    category = 'ippoc_provider'
                elif provider == 'groq':
                    category = 'groq_provider'
                elif provider in ['fixed', 'dev', 'final']:
                    category = 'fixed_issues'
                break
        
        # Create target directory
        target_dir = self.organized_path / "by_type" / category
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        target_file = target_dir / log_file.name
        shutil.copy2(log_file, target_file)
        
        # Also organize by date and status
        self._organize_by_date_and_status(target_file, entries)
    
    def _organize_by_date_and_status(self, log_file: Path, entries: List[LogEntry]):
        """Organize log file by date and status"""
        # By date
        dates = set()
        for entry in entries:
            if entry.timestamp:
                try:
                    date_obj = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00'))
                    dates.add(date_obj.date())
                except:
                    pass
        
        for date in dates:
            date_dir = self.organized_path / "by_date" / date.isoformat()
            date_dir.mkdir(parents=True, exist_ok=True)
            target = date_dir / log_file.name
            if not target.exists():
                shutil.copy2(log_file, target)
        
        # By status
        has_errors = any(entry.level == 'ERROR' for entry in entries)
        status_dir = "problematic" if has_errors else "working"
        status_path = self.organized_path / "by_status" / status_dir
        status_path.mkdir(parents=True, exist_ok=True)
        target = status_path / log_file.name
        if not target.exists():
            shutil.copy2(log_file, target)
    
    def get_health_metrics(self) -> LogHealthMetrics:
        """Calculate comprehensive health metrics for the log system"""
        if not self.organized_path.exists():
            raise FileNotFoundError("No organized logs found")
        
        # Collect all log entries
        all_entries = []
        file_sizes = []
        file_dates = []
        provider_counts = defaultdict(int)
        
        for log_file in self.organized_path.rglob("*.log"):
            try:
                entries = self.log_manager.parse_log_file(log_file)
                all_entries.extend(entries)
                file_sizes.append(log_file.stat().st_size)
                
                # Count by provider
                filename = log_file.name.lower()
                for provider in self.providers:
                    if provider in filename:
                        provider_counts[provider] += 1
                        break
                
                # Get file modification time as proxy for log dates
                file_dates.append(datetime.fromtimestamp(log_file.stat().st_mtime))
                        
            except Exception as e:
                print(f"Error processing {log_file}: {e}")
        
        if not all_entries:
            raise ValueError("No log entries found")
        
        # Calculate metrics
        total_entries = len(all_entries)
        error_entries = len([e for e in all_entries if e.level == 'ERROR'])
        error_rate = (error_entries / total_entries * 100) if total_entries > 0 else 0
        
        timestamps = [e.timestamp for e in all_entries if e.timestamp]
        oldest = min(timestamps) if timestamps else "Unknown"
        newest = max(timestamps) if timestamps else "Unknown"
        
        avg_entries = total_entries / len(list(self.organized_path.rglob("*.log")))
        largest_file = max(file_sizes) / (1024 * 1024) if file_sizes else 0
        
        # Error pattern analysis
        error_messages = [e.message for e in all_entries if e.level == 'ERROR']
        error_counter = Counter(error_messages)
        top_errors = error_counter.most_common(10)
        
        # Generate recommendations
        recommendations = []
        if error_rate > 5:
            recommendations.append(f"High error rate ({error_rate:.1f}%) - investigate critical issues")
        if provider_counts['ippoc'] > provider_counts['ollama']:
            recommendations.append("IPPOC provider heavily used - consider load balancing")
        if largest_file > 10:
            recommendations.append(f"Large log files detected ({largest_file:.1f}MB) - consider rotation")
            
        return LogHealthMetrics(
            total_files=len(list(self.organized_path.rglob("*.log"))),
            total_entries=total_entries,
            error_rate=error_rate,
            avg_entries_per_file=avg_entries,
            largest_file_mb=largest_file,
            oldest_entry=oldest,
            newest_entry=newest,
            file_count_by_provider=dict(provider_counts),
            error_patterns=top_errors,
            recommendations=recommendations
        )
    
    def archive_old_logs(self, days_old: int = 30) -> int:
        """Archive logs older than specified days"""
        archived_count = 0
        cutoff_date = datetime.now() - timedelta(days=days_old)
        archive_dir = self.organized_path / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        for log_file in self.organized_path.rglob("*.log"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                # Create dated archive structure
                file_date = datetime.fromtimestamp(log_file.stat().st_mtime).date()
                year_month = file_date.strftime("%Y-%m")
                target_dir = archive_dir / year_month
                target_dir.mkdir(exist_ok=True)
                
                target_file = target_dir / log_file.name
                if not target_file.exists():
                    shutil.move(str(log_file), str(target_file))
                    archived_count += 1
                    
        return archived_count
    
    def clean_duplicate_logs(self) -> tuple[int, float]:
        """Remove duplicate log files and return count and space saved"""
        seen_hashes = {}
        removed_count = 0
        space_saved = 0.0
        
        for log_file in self.organized_path.rglob("*.log"):
            try:
                # Calculate file hash
                hash_md5 = hashlib.md5()
                with open(log_file, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)
                file_hash = hash_md5.hexdigest()
                
                if file_hash in seen_hashes:
                    # Duplicate found
                    space_saved += log_file.stat().st_size / (1024 * 1024)
                    log_file.unlink()
                    removed_count += 1
                else:
                    seen_hashes[file_hash] = log_file
                    
            except Exception as e:
                print(f"Error processing {log_file}: {e}")
                
        return removed_count, space_saved
    
    def compress_large_logs(self, size_threshold_mb: float = 5.0) -> int:
        """Compress log files larger than threshold"""
        import gzip
        
        compressed_count = 0
        threshold_bytes = size_threshold_mb * 1024 * 1024
        
        for log_file in self.organized_path.rglob("*.log"):
            if log_file.stat().st_size > threshold_bytes:
                try:
                    # Create gzipped version
                    gz_file = log_file.with_suffix('.log.gz')
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(gz_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Remove original if compression successful
                    if gz_file.exists():
                        space_saved = log_file.stat().st_size - gz_file.stat().st_size
                        if space_saved > 0:
                            log_file.unlink()
                            compressed_count += 1
                            
                except Exception as e:
                    print(f"Error compressing {log_file}: {e}")
                    
        return compressed_count
    
    def generate_maintenance_report(self) -> LogMaintenanceReport:
        """Generate comprehensive maintenance report"""
        timestamp = datetime.now().isoformat()
        
        # Get health metrics
        try:
            health_metrics = self.get_health_metrics()
        except Exception as e:
            print(f"Error getting health metrics: {e}")
            health_metrics = None
        
        # Perform maintenance operations
        duplicates_removed, space_saved = self.clean_duplicate_logs()
        archived_count = self.archive_old_logs(days_old=30)
        compressed_count = self.compress_large_logs(size_threshold_mb=2.0)
        
        files_processed = len(list(self.organized_path.rglob("*.log")))
        
        return LogMaintenanceReport(
            timestamp=timestamp,
            files_processed=files_processed,
            duplicates_removed=duplicates_removed,
            files_archived=archived_count,
            space_saved_mb=space_saved,
            health_metrics=health_metrics
        )
    
    def create_dashboard_summary(self) -> Dict:
        """Create a summary suitable for dashboard display"""
        try:
            health = self.get_health_metrics()
            
            summary = {
                "timestamp": datetime.now().isoformat(),
                "overview": {
                    "total_files": health.total_files,
                    "total_entries": health.total_entries,
                    "error_rate": f"{health.error_rate:.2f}%",
                    "providers_active": len(health.file_count_by_provider)
                },
                "provider_distribution": health.file_count_by_provider,
                "top_errors": [{"message": msg[:50], "count": count} 
                              for msg, count in health.error_patterns[:5]],
                "recommendations": health.recommendations,
                "storage": {
                    "largest_file_mb": round(health.largest_file_mb, 2),
                    "avg_entries_per_file": round(health.avg_entries_per_file, 1)
                }
            }
            
            return summary
            
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}


def main():
    """Main function for enhanced log management"""
    print("🚀 Enhanced Open Cortex Log Manager")
    print("=" * 50)
    
    manager = EnhancedLogManager()
    
    # Check for new logs
    print("\n🔍 Scanning for new logs...")
    new_count = manager.process_new_logs()
    if new_count > 0:
        print(f"✅ Processed {new_count} new log files")
    else:
        print("✅ No new logs found")
    
    # Generate health report
    print("\n📊 Generating health metrics...")
    try:
        health = manager.get_health_metrics()
        print(f"Total Files: {health.total_files}")
        print(f"Total Entries: {health.total_entries:,}")
        print(f"Error Rate: {health.error_rate:.2f}%")
        print(f"Largest File: {health.largest_file_mb:.2f} MB")
        print(f"Providers: {', '.join(health.file_count_by_provider.keys())}")
        
        if health.recommendations:
            print("\n💡 Recommendations:")
            for rec in health.recommendations:
                print(f"  • {rec}")
                
    except Exception as e:
        print(f"❌ Error generating health metrics: {e}")
    
    # Generate maintenance report
    print("\n🔧 Running maintenance...")
    try:
        report = manager.generate_maintenance_report()
        print(f"Files processed: {report.files_processed}")
        print(f"Duplicates removed: {report.duplicates_removed}")
        print(f"Files archived: {report.files_archived}")
        print(f"Space saved: {report.space_saved_mb:.2f} MB")
        
        # Save report
        report_file = manager.organized_path / f"maintenance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
        print(f"✅ Maintenance report saved to {report_file}")
        
    except Exception as e:
        print(f"❌ Error during maintenance: {e}")
    
    # Create dashboard summary
    print("\n📋 Creating dashboard summary...")
    try:
        summary = manager.create_dashboard_summary()
        summary_file = manager.organized_path / "dashboard_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"✅ Dashboard summary saved to {summary_file}")
    except Exception as e:
        print(f"❌ Error creating dashboard summary: {e}")

if __name__ == "__main__":
    main()