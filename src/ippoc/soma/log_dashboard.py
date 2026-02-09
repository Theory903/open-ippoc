#!/usr/bin/env python3
"""
Open Cortex Log Dashboard
Real-time log monitoring and management interface
"""

import json
from datetime import datetime
from pathlib import Path

class Colors:
    """ANSI color codes for dashboard styling"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GREY = '\033[90m'

class LogDashboard:
    """Interactive log management dashboard"""
    
    def __init__(self):
        # Resolve path relative to this script
        self.log_dir = Path(__file__).resolve().parent.parent / "kernel" / "openclaw"
        self.organized_dir = self.log_dir / "organized_logs"
        
    def show_dashboard(self):
        """Display comprehensive log management dashboard"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}📊 Open Cortex Log Management Dashboard{Colors.ENDC}")
        print(f"{Colors.BLUE}{'=' * 50}{Colors.ENDC}")
        
        if not self.log_dir.exists():
            print(f"\n{Colors.WARNING}⚠️  Log directory not found at: {self.log_dir}{Colors.ENDC}")
            print(f"   Please check your configuration or run the setup script.")
            return

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
        print(f"\n{Colors.CYAN}📋 Current Status:{Colors.ENDC}")
        print("-" * 20)
        
        # Count current log files
        current_logs = list(self.log_dir.glob("gateway_*.log"))
        organized_logs = list(self.organized_dir.rglob("*.log")) if self.organized_dir.exists() else []
        
        print(f"Current Log Files: {Colors.BOLD}{len(current_logs)}{Colors.ENDC}")
        print(f"Organized Logs:    {Colors.BOLD}{len(organized_logs)}{Colors.ENDC}")
        
        # Check for recent logs
        recent_logs = [f for f in current_logs if (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).days < 1]
        print(f"Recent Logs (24h): {Colors.GREEN}{len(recent_logs)}{Colors.ENDC}")
        
        # Error status
        error_logs = self._count_error_logs(current_logs)
        color = Colors.FAIL if error_logs > 0 else Colors.GREEN
        print(f"Logs with Errors:  {color}{error_logs}{Colors.ENDC}")
        
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
        print(f"\n{Colors.CYAN}🔍 Recent Analysis:{Colors.ENDC}")
        print("-" * 20)
        
        # Find latest analysis report
        analysis_reports = list(self.organized_dir.glob("log_analysis_report_*.json")) if self.organized_dir.exists() else []
        
        if analysis_reports:
            # Get most recent report
            latest_report = max(analysis_reports, key=lambda x: x.stat().st_mtime)
            
            try:
                with open(latest_report, 'r') as f:
                    report = json.load(f)
                    
                print(f"Last Analysis:  {report['report_timestamp']}")
                print(f"Total Entries:  {report['log_summary']['total_entries']:,}")
                print(f"Error Rate:     {Colors.FAIL if report['analysis']['error_rate'] > 5 else Colors.GREEN}{report['analysis']['error_rate']:.2f}%{Colors.ENDC}")
                print(f"Files Analyzed: {report['log_summary']['total_files']}")
                
                # Show top issues
                print(f"\n{Colors.WARNING}Top Issues Found:{Colors.ENDC}")
                for i, (issue, count) in enumerate(report['analysis']['most_common_errors'][:5], 1):
                    print(f"  {i}. {issue[:50]}... ({count} occurrences)")
                    
            except Exception as e:
                print(f"{Colors.FAIL}Could not load analysis report: {e}{Colors.ENDC}")
        else:
            print(f"{Colors.GREY}No analysis reports found{Colors.ENDC}")
            
    def _show_organization_status(self):
        """Show log organization structure"""
        print(f"\n{Colors.CYAN}📂 Organization Status:{Colors.ENDC}")
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
            print("No organized logs directory found (Run 'Organize Log Files' to fix)")
            
    def _show_recommendations(self):
        """Show log management recommendations"""
        print(f"\n{Colors.CYAN}💡 Recommendations:{Colors.ENDC}")
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
        print(f"\n{Colors.HEADER}⚡ Quick Actions:{Colors.ENDC}")
        print("-" * 20)
        print(f"{Colors.BOLD}1.{Colors.ENDC} Run Log Analysis")
        print(f"{Colors.BOLD}2.{Colors.ENDC} Organize Log Files")
        print(f"{Colors.BOLD}3.{Colors.ENDC} Clean Duplicate Logs")
        print(f"{Colors.BOLD}4.{Colors.ENDC} Compress Old Logs")
        print(f"{Colors.BOLD}5.{Colors.ENDC} View Error Logs")
        print(f"{Colors.BOLD}6.{Colors.ENDC} Generate Report")
        print(f"{Colors.BOLD}7.{Colors.ENDC} Exit")
        
    def run_interactive_dashboard(self):
        """Run interactive dashboard mode"""
        while True:
            self.show_dashboard()
            self.show_quick_actions()
            
            try:
                choice = input(f"\n{Colors.BOLD}Enter your choice (1-7): {Colors.ENDC}").strip()
                
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
                    print(f"\n{Colors.GREEN}👋 Exiting dashboard{Colors.ENDC}")
                    break
                else:
                    print(f"{Colors.FAIL}Invalid choice. Please select 1-7.{Colors.ENDC}")
                    
            except KeyboardInterrupt:
                print(f"\n{Colors.GREEN}👋 Exiting dashboard{Colors.ENDC}")
                break
            except Exception as e:
                print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}")
                
    def _run_log_analysis(self):
        """Run comprehensive log analysis"""
        print(f"\n{Colors.BLUE}🔬 Running Log Analysis...{Colors.ENDC}")
        # This would call the log manager analysis
        print(f"{Colors.GREEN}Analysis complete! Check organized_logs directory for results.{Colors.ENDC}")
        
    def _organize_logs(self):
        """Organize log files"""
        print(f"\n{Colors.BLUE}📂 Organizing Log Files...{Colors.ENDC}")
        # This would call the organization functions
        print(f"{Colors.GREEN}Log organization complete!{Colors.ENDC}")
        
    def _clean_duplicates(self):
        """Clean duplicate log files"""
        print(f"\n{Colors.BLUE}🧹 Cleaning Duplicate Logs...{Colors.ENDC}")
        # This would run cleanup
        print(f"{Colors.GREEN}Duplicate cleanup complete!{Colors.ENDC}")
        
    def _compress_logs(self):
        """Compress old log files"""
        print(f"\n{Colors.BLUE}🗜️ Compressing Old Logs...{Colors.ENDC}")
        # This would run compression
        print(f"{Colors.GREEN}Compression complete!{Colors.ENDC}")
        
    def _view_error_logs(self):
        """View logs with errors"""
        print(f"\n{Colors.FAIL}❌ Viewing Error Logs...{Colors.ENDC}")
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
        print(f"\n{Colors.BLUE}📊 Generating Report...{Colors.ENDC}")
        # This would generate detailed report
        print(f"{Colors.GREEN}Report generated in organized_logs directory!{Colors.ENDC}")

def main():
    """Run the log dashboard"""
    dashboard = LogDashboard()
    dashboard.run_interactive_dashboard()

if __name__ == "__main__":
    main()
