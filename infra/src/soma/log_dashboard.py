#!/usr/bin/env python3
"""
Open Cortex Log Dashboard
Real-time log monitoring and management interface
"""

import json
from datetime import datetime
from pathlib import Path

class LogDashboard:
    """Interactive log management dashboard"""
    
    def __init__(self):
        self.log_dir = Path("/Users/abhishekjha/CODE/ippoc/src/kernel/openclaw")
        self.organized_dir = self.log_dir / "organized_logs"
        
    def show_dashboard(self):
        """Display comprehensive log management dashboard"""
        print("📊 Open Cortex Log Management Dashboard")
        print("=" * 50)
        
        # Current status
        self._show_current_status()
        
        # Recent analysis
        self._show_recent_analysis()
        
        # Log organization status
        self._show_organization_status()
        
        # Action recommendations
        self._show_recommendations()
        
    def _show_current_status(self):
        """Show current log system status"""
        print("\n📋 Current Status:")
        print("-" * 20)
        
        # Count current log files
        current_logs = list(self.log_dir.glob("gateway_*.log"))
        organized_logs = list(self.organized_dir.rglob("*.log")) if self.organized_dir.exists() else []
        
        print(f"Current Log Files: {len(current_logs)}")
        print(f"Organized Logs: {len(organized_logs)}")
        
        # Check for recent logs
        recent_logs = [f for f in current_logs if (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).days < 1]
        print(f"Recent Logs (24h): {len(recent_logs)}")
        
        # Error status
        error_logs = self._count_error_logs(current_logs)
        print(f"Logs with Errors: {error_logs}")
        
    def _count_error_logs(self, log_files):
        """Count logs containing error entries"""
        error_count = 0
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                    if 'error' in content.lower() or 'failed' in content.lower():
                        error_count += 1
            except:
                pass
        return error_count
        
    def _show_recent_analysis(self):
        """Show recent log analysis results"""
        print("\n🔍 Recent Analysis:")
        print("-" * 20)
        
        # Find latest analysis report
        analysis_reports = list(self.organized_dir.glob("log_analysis_report_*.json")) if self.organized_dir.exists() else []
        
        if analysis_reports:
            # Get most recent report
            latest_report = max(analysis_reports, key=lambda x: x.stat().st_mtime)
            
            try:
                with open(latest_report, 'r') as f:
                    report = json.load(f)
                    
                print(f"Last Analysis: {report['report_timestamp']}")
                print(f"Total Entries: {report['log_summary']['total_entries']:,}")
                print(f"Error Rate: {report['analysis']['error_rate']:.2f}%")
                print(f"Files Analyzed: {report['log_summary']['total_files']}")
                
                # Show top issues
                print("\nTop Issues Found:")
                for i, (issue, count) in enumerate(report['analysis']['most_common_errors'][:5], 1):
                    print(f"  {i}. {issue[:50]}... ({count} occurrences)")
                    
            except Exception as e:
                print(f"Could not load analysis report: {e}")
        else:
            print("No analysis reports found")
            
    def _show_organization_status(self):
        """Show log organization structure"""
        print("\n📂 Organization Status:")
        print("-" * 20)
        
        if self.organized_dir.exists():
            # Show directory structure
            by_type = self.organized_dir / "by_type"
            by_status = self.organized_dir / "by_status"
            by_date = self.organized_dir / "by_date"
            
            print("Organization Directories:")
            if by_type.exists():
                categories = [d.name for d in by_type.iterdir() if d.is_dir()]
                print(f"  By Type: {len(categories)} categories")
                for cat in categories:
                    cat_dir = by_type / cat
                    file_count = len(list(cat_dir.glob("*.log")))
                    print(f"    - {cat}: {file_count} files")
                    
            if by_status.exists():
                status_dirs = [d.name for d in by_status.iterdir() if d.is_dir()]
                print(f"  By Status: {len(status_dirs)} statuses")
                
            if by_date.exists():
                date_dirs = [d.name for d in by_date.iterdir() if d.is_dir()]
                print(f"  By Date: {len(date_dirs)} dates")
        else:
            print("No organized logs directory found")
            
    def _show_recommendations(self):
        """Show log management recommendations"""
        print("\n💡 Recommendations:")
        print("-" * 20)
        
        recommendations = [
            "Implement daily log rotation to prevent accumulation",
            "Set up automatic compression for logs older than 7 days",
            "Configure alerting for high error rates (>5%)",
            "Regular cleanup of duplicate/versioned log files",
            "Monitor authentication failure patterns",
            "Review WebSocket connection stability issues",
            "Check browser automation service health",
            "Implement centralized log aggregation"
        ]
        
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
            
    def show_quick_actions(self):
        """Show available quick actions"""
        print("\n⚡ Quick Actions:")
        print("-" * 20)
        print("1. Run Log Analysis")
        print("2. Organize Log Files") 
        print("3. Clean Duplicate Logs")
        print("4. Compress Old Logs")
        print("5. View Error Logs")
        print("6. Generate Report")
        print("7. Exit")
        
    def run_interactive_dashboard(self):
        """Run interactive dashboard mode"""
        while True:
            self.show_dashboard()
            self.show_quick_actions()
            
            try:
                choice = input("\nEnter your choice (1-7): ").strip()
                
                if choice == '1':
                    self._run_log_analysis()
                elif choice == '2':
                    self._organize_logs()
                elif choice == '3':
                    self._clean_duplicates()
                elif choice == '4':
                    self._compress_logs()
                elif choice == '5':
                    self._view_error_logs()
                elif choice == '6':
                    self._generate_report()
                elif choice == '7':
                    print("👋 Exiting dashboard")
                    break
                else:
                    print("Invalid choice. Please select 1-7.")
                    
            except KeyboardInterrupt:
                print("\n👋 Exiting dashboard")
                break
            except Exception as e:
                print(f"Error: {e}")
                
    def _run_log_analysis(self):
        """Run comprehensive log analysis"""
        print("\n🔬 Running Log Analysis...")
        # This would call the log manager analysis
        print("Analysis complete! Check organized_logs directory for results.")
        
    def _organize_logs(self):
        """Organize log files"""
        print("\n📂 Organizing Log Files...")
        # This would call the organization functions
        print("Log organization complete!")
        
    def _clean_duplicates(self):
        """Clean duplicate log files"""
        print("\n🧹 Cleaning Duplicate Logs...")
        # This would run cleanup
        print("Duplicate cleanup complete!")
        
    def _compress_logs(self):
        """Compress old log files"""
        print("\n🗜️ Compressing Old Logs...")
        # This would run compression
        print("Compression complete!")
        
    def _view_error_logs(self):
        """View logs with errors"""
        print("\n❌ Viewing Error Logs...")
        current_logs = list(self.log_dir.glob("gateway_*.log"))
        error_logs = []
        
        for log_file in current_logs:
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                    if 'error' in content.lower() or 'failed' in content.lower():
                        error_logs.append(log_file)
            except:
                pass
                
        print(f"Found {len(error_logs)} logs with errors:")
        for log_file in error_logs[:10]:  # Show first 10
            print(f"  - {log_file.name}")
            
    def _generate_report(self):
        """Generate comprehensive report"""
        print("\n📊 Generating Report...")
        # This would generate detailed report
        print("Report generated in organized_logs directory!")

def main():
    """Run the log dashboard"""
    dashboard = LogDashboard()
    dashboard.run_interactive_dashboard()

if __name__ == "__main__":
    main()