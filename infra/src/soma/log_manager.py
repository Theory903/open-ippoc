#!/usr/bin/env python3
"""
Open Cortex Log Management System
Centralized log management, rotation, and analysis for OpenClaw gateway logs
"""

import os
import json
import logging
import shutil
import gzip
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LogEntry:
    """Represents a parsed log entry"""
    timestamp: str
    level: str
    component: str
    message: str
    details: Dict[str, Any]

class OpenCortexLogManager:
    """Manages OpenClaw/Open Cortex log files"""
    
    def __init__(self, log_directory: str = "/Users/abhishekjha/CODE/ippoc/src/kernel/openclaw"):
        self.log_directory = Path(log_directory)
        self.log_files = []
        self.parsed_logs = []
        self.log_stats = {}
        
        # Setup log organization structure
        self.organized_logs_dir = self.log_directory / "organized_logs"
        self.organized_logs_dir.mkdir(exist_ok=True)
        
        self._scan_log_files()
        self._setup_log_categories()
        
    def _scan_log_files(self):
        """Scan and catalog all log files"""
        logger.info("🔍 Scanning log files...")
        
        # Common log file patterns
        log_patterns = [
            "gateway_*.log",
            "gateway_*_*.log",
            "*.log"
        ]
        
        self.log_files = []
        for pattern in log_patterns:
            for log_file in self.log_directory.glob(pattern):
                if log_file.is_file() and log_file.suffix == '.log':
                    file_stat = log_file.stat()
                    self.log_files.append({
                        'path': log_file,
                        'size': file_stat.st_size,
                        'modified': datetime.fromtimestamp(file_stat.st_mtime),
                        'name': log_file.name
                    })
        
        logger.info(f"Found {len(self.log_files)} log files")
        
    def _setup_log_categories(self):
        """Setup log categorization rules"""
        self.log_categories = {
            'authentication': ['token', 'auth', 'unauthorized', 'device.pair'],
            'connection': ['ws', 'connect', 'disconnect', 'listening'],
            'system': ['gateway', 'heartbeat', 'shutdown', 'signal'],
            'error': ['error', 'failed', 'exception', 'mismatch'],
            'browser': ['browser', 'canvas', 'webchat'],
            'agent': ['agent', 'model', 'identity', 'session'],
            'node': ['node.list', 'node.status'],
            'chat': ['chat', 'message', 'send', 'history'],
            'config': ['config', 'settings', 'schema'],
            'diagnostic': ['diagnostic', 'lane', 'task']
        }
        
    def parse_log_file(self, log_file_path: Path) -> List[LogEntry]:
        """Parse a log file into structured entries"""
        entries = []
        
        try:
            with open(log_file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    entry = self._parse_log_line(line.strip(), line_num)
                    if entry:
                        entries.append(entry)
        except Exception as e:
            logger.error(f"Failed to parse {log_file_path}: {e}")
            
        return entries
        
    def _parse_log_line(self, line: str, line_number: int) -> Optional[LogEntry]:
        """Parse a single log line"""
        if not line:
            return None
            
        try:
            # Extract timestamp (ISO format)
            timestamp_match = line[:24]  # YYYY-MM-DDTHH:MM:SS.sssZ
            if len(timestamp_match) >= 24:
                timestamp = timestamp_match
                message_start = 25
            else:
                timestamp = datetime.now().isoformat()
                message_start = 0
                
            # Extract log content
            log_content = line[message_start:].strip() if message_start < len(line) else line
            
            # Determine log level and component
            level = "INFO"
            component = "unknown"
            
            # Identify component from message patterns
            if '[gateway]' in log_content:
                component = "gateway"
            elif '[ws]' in log_content:
                component = "websocket"
            elif '[browser' in log_content:
                component = "browser"
            elif '[agent' in log_content:
                component = "agent"
            elif '[diagnostic]' in log_content:
                component = "diagnostic"
                
            # Identify error levels
            if 'error' in log_content.lower() or 'failed' in log_content.lower():
                level = "ERROR"
            elif 'warning' in log_content.lower() or 'warn' in log_content.lower():
                level = "WARNING"
                
            return LogEntry(
                timestamp=timestamp,
                level=level,
                component=component,
                message=log_content,
                details={
                    'line_number': line_number,
                    'raw_line': line
                }
            )
            
        except Exception as e:
            logger.debug(f"Failed to parse line: {line[:50]}... Error: {e}")
            return None
            
    def categorize_logs(self) -> Dict[str, List[LogEntry]]:
        """Categorize all parsed logs"""
        categorized = {category: [] for category in self.log_categories.keys()}
        categorized['uncategorized'] = []
        
        for entry in self.parsed_logs:
            categorized_entry = False
            message_lower = entry.message.lower()
            
            for category, keywords in self.log_categories.items():
                if any(keyword in message_lower for keyword in keywords):
                    categorized[category].append(entry)
                    categorized_entry = True
                    break
                    
            if not categorized_entry:
                categorized['uncategorized'].append(entry)
                
        return categorized
        
    def analyze_log_patterns(self) -> Dict[str, Any]:
        """Analyze log patterns and generate insights"""
        analysis = {
            'total_entries': len(self.parsed_logs),
            'by_component': {},
            'by_level': {},
            'by_category': {},
            'error_rate': 0,
            'most_common_errors': [],
            'timeline_analysis': {}
        }
        
        # Component analysis
        for entry in self.parsed_logs:
            analysis['by_component'][entry.component] = analysis['by_component'].get(entry.component, 0) + 1
            analysis['by_level'][entry.level] = analysis['by_level'].get(entry.level, 0) + 1
            
        # Error rate calculation
        error_count = analysis['by_level'].get('ERROR', 0)
        total_count = analysis['total_entries']
        analysis['error_rate'] = (error_count / max(1, total_count)) * 100
        
        # Categorize logs
        categorized = self.categorize_logs()
        for category, entries in categorized.items():
            analysis['by_category'][category] = len(entries)
            
        # Most common errors
        error_entries = [e for e in self.parsed_logs if e.level == 'ERROR']
        error_messages = {}
        for entry in error_entries:
            msg_key = entry.message.split(':')[0][:50]  # First 50 chars as key
            error_messages[msg_key] = error_messages.get(msg_key, 0) + 1
            
        analysis['most_common_errors'] = sorted(
            error_messages.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return analysis
        
    def organize_log_files(self):
        """Organize log files into structured directories"""
        logger.info("📂 Organizing log files...")
        
        # Create organization structure
        structure = {
            'by_date': self.organized_logs_dir / "by_date",
            'by_type': self.organized_logs_dir / "by_type",
            'by_status': self.organized_logs_dir / "by_status",
            'parsed_json': self.organized_logs_dir / "parsed_json"
        }
        
        for path in structure.values():
            path.mkdir(exist_ok=True)
            
        # Organize by date
        for log_file in self.log_files:
            date_str = log_file['modified'].strftime('%Y-%m-%d')
            date_dir = structure['by_date'] / date_str
            date_dir.mkdir(exist_ok=True)
            
            # Move file
            target_path = date_dir / log_file['name']
            if not target_path.exists():
                shutil.copy2(log_file['path'], target_path)
                
        # Organize by type (based on filename patterns)
        type_mapping = {
            'gateway_dev': 'development',
            'gateway_final': 'production',
            'gateway_fixed': 'fixed_issues',
            'gateway_groq': 'groq_provider',
            'gateway_ollama': 'ollama_provider',
            'gateway_ippoc': 'ippoc_provider',
            'gateway_kimi': 'kimi_provider'
        }
        
        for log_file in self.log_files:
            file_type = 'other'
            for pattern, category in type_mapping.items():
                if pattern in log_file['name']:
                    file_type = category
                    break
                    
            type_dir = structure['by_type'] / file_type
            type_dir.mkdir(exist_ok=True)
            
            target_path = type_dir / log_file['name']
            if not target_path.exists():
                shutil.copy2(log_file['path'], target_path)
                
        # Organize by status (working vs problematic)
        working_logs = []
        problematic_logs = []
        
        for log_file in self.log_files:
            # Parse log to determine status
            entries = self.parse_log_file(log_file['path'])
            error_entries = [e for e in entries if e.level == 'ERROR']
            
            if len(error_entries) > 10:  # Arbitrary threshold
                problematic_logs.append(log_file)
            else:
                working_logs.append(log_file)
                
        # Save status organization
        status_dirs = {
            'working': structure['by_status'] / "working",
            'problematic': structure['by_status'] / "problematic"
        }
        
        for name, path in status_dirs.items():
            path.mkdir(exist_ok=True)
            
        for log_file in working_logs:
            target_path = status_dirs['working'] / log_file['name']
            if not target_path.exists():
                shutil.copy2(log_file['path'], target_path)
                
        for log_file in problematic_logs:
            target_path = status_dirs['problematic'] / log_file['name']
            if not target_path.exists():
                shutil.copy2(log_file['path'], target_path)
                
        logger.info("✅ Log organization complete")
        
    def compress_old_logs(self, days_old: int = 7):
        """Compress log files older than specified days"""
        logger.info(f"🗜️ Compressing logs older than {days_old} days...")
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        compressed_count = 0
        
        for log_file in self.log_files:
            if log_file['modified'] < cutoff_date:
                # Check if already compressed
                gz_path = log_file['path'].with_suffix('.log.gz')
                if not gz_path.exists():
                    try:
                        with open(log_file['path'], 'rb') as f_in:
                            with gzip.open(gz_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                                
                        # Remove original file
                        log_file['path'].unlink()
                        compressed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to compress {log_file['path']}: {e}")
                        
        logger.info(f"Compressed {compressed_count} log files")
        
    def generate_log_report(self) -> Dict[str, Any]:
        """Generate comprehensive log analysis report"""
        logger.info("📊 Generating log analysis report...")
        
        # Parse all logs
        all_entries = []
        for log_file in self.log_files:
            entries = self.parse_log_file(log_file['path'])
            all_entries.extend(entries)
            
        self.parsed_logs = all_entries
        
        # Generate analysis
        analysis = self.analyze_log_patterns()
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'log_summary': {
                'total_files': len(self.log_files),
                'total_entries': len(all_entries),
                'date_range': {
                    'oldest': min(f['modified'] for f in self.log_files).isoformat(),
                    'newest': max(f['modified'] for f in self.log_files).isoformat()
                },
                'total_size_mb': sum(f['size'] for f in self.log_files) / (1024 * 1024)
            },
            'analysis': analysis,
            'recommendations': self._generate_recommendations(analysis)
        }
        
        # Save report
        report_path = self.organized_logs_dir / f"log_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Report saved to: {report_path}")
        return report
        
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on log analysis"""
        recommendations = []
        
        # Error rate recommendations
        if analysis['error_rate'] > 5:
            recommendations.append("High error rate detected - investigate recurring errors")
            
        # Authentication issues
        auth_errors = analysis['by_category'].get('authentication', 0)
        if auth_errors > 50:
            recommendations.append("Authentication failures are frequent - check token configuration")
            
        # Connection stability
        connection_issues = analysis['by_category'].get('connection', 0)
        if connection_issues > 100:
            recommendations.append("Connection instability detected - review WebSocket configuration")
            
        # Browser service issues
        browser_issues = analysis['by_category'].get('browser', 0)
        if browser_issues > 30:
            recommendations.append("Browser service problems - check browser automation setup")
            
        return recommendations
        
    def cleanup_duplicate_logs(self):
        """Remove duplicate log files"""
        logger.info("🧹 Cleaning up duplicate logs...")
        
        # Group logs by base name pattern
        log_groups = {}
        for log_file in self.log_files:
            # Extract base name without version/number suffix
            base_name = log_file['name']
            for suffix in ['_v2', '_v3', '_v4', '_v5', '_v6', '_v7', '_v8', '_v9']:
                if suffix in base_name:
                    base_name = base_name.replace(suffix, '')
                    break
                    
            if base_name not in log_groups:
                log_groups[base_name] = []
            log_groups[base_name].append(log_file)
            
        # Keep only the most recent file in each group
        files_to_delete = []
        for base_name, group in log_groups.items():
            if len(group) > 1:
                # Sort by modification time, keep newest
                group.sort(key=lambda x: x['modified'], reverse=True)
                files_to_delete.extend(group[1:])  # Keep first (newest), delete rest
                
        # Delete duplicates
        deleted_count = 0
        for log_file in files_to_delete:
            try:
                log_file['path'].unlink()
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete {log_file['path']}: {e}")
                
        logger.info(f"Deleted {deleted_count} duplicate log files")
        
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get current log statistics"""
        total_size = sum(f['size'] for f in self.log_files)
        oldest_file = min(f['modified'] for f in self.log_files)
        newest_file = max(f['modified'] for f in self.log_files)
        
        return {
            'total_log_files': len(self.log_files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'date_range': {
                'oldest': oldest_file.strftime('%Y-%m-%d'),
                'newest': newest_file.strftime('%Y-%m-%d')
            },
            'organized_directory': str(self.organized_logs_dir)
        }

# Global log manager instance
log_manager = OpenCortexLogManager()

def main():
    """Run the log management demonstration"""
    print("📊 Open Cortex Log Management System")
    print("=" * 45)
    
    # Show current statistics
    stats = log_manager.get_log_statistics()
    print(f"Current Log Statistics:")
    print(f"  Total Files: {stats['total_log_files']}")
    print(f"  Total Size: {stats['total_size_mb']} MB")
    print(f"  Date Range: {stats['date_range']['oldest']} to {stats['date_range']['newest']}")
    print(f"  Organized Dir: {stats['organized_directory']}")
    
    # Generate analysis report
    print("\n🔍 Generating Log Analysis...")
    report = log_manager.generate_log_report()
    
    print(f"Analysis Complete!")
    print(f"  Total Entries Analyzed: {report['log_summary']['total_entries']}")
    print(f"  Error Rate: {report['analysis']['error_rate']:.2f}%")
    print(f"  Recommendations: {len(report['recommendations'])}")
    
    # Show key findings
    print(f"\n📋 Key Findings:")
    top_categories = sorted(
        report['analysis']['by_category'].items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:5]
    
    for category, count in top_categories:
        print(f"  {category}: {count} entries")
        
    # Organize logs
    print(f"\n📂 Organizing Log Files...")
    log_manager.organize_log_files()
    
    # Cleanup duplicates
    print(f"🧹 Cleaning Duplicate Logs...")
    log_manager.cleanup_duplicate_logs()
    
    print(f"\n✅ Log Management Complete!")

if __name__ == "__main__":
    main()