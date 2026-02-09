#!/usr/bin/env python3
"""
Infrastructure Chaos Simulation for IPPOC v1.0.2
Tests system resilience against:
1. Redis flapping
2. Database corruption
3. Disk full scenario
4. Network blackhole
5. Clock skew

Generates chaos/infra_resilience_report.md
"""

import os
import subprocess
import time
import requests
import json
import shutil
import tempfile
from pathlib import Path
import random
import string


class ChaosSimulator:
    def __init__(self):
        self.report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": "v1.0.2",
            "scenarios": [],
            "overall_status": "PASS"
        }
        self.chaos_dir = Path("chaos")
        self.chaos_dir.mkdir(exist_ok=True)
        self.services = self._detect_running_services()

    def _detect_running_services(self):
        """Detect which services are running"""
        services = []
        try:
            docker_ps = subprocess.check_output(
                ["docker", "ps", "--format", "{{.Names}}"], text=True
            )
            for name in docker_ps.strip().split("\n"):
                if "ippoc" in name or "cortex" in name or "memory" in name or "openclaw" in name:
                    services.append(name)
        except Exception:
            pass

        return services

    def _log_scenario(self, scenario, status, observations):
        self.report_data["scenarios"].append({
            "scenario": scenario,
            "status": status,
            "observations": observations
        })
        if status == "FAIL":
            self.report_data["overall_status"] = "FAIL"

    def _health_check(self, endpoint="http://localhost:8000/health"):
        """Check system health"""
        try:
            response = requests.get(endpoint, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def _create_large_file(self, size_gb=1):
        """Create a large temporary file to simulate disk full scenario"""
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, dir=self.chaos_dir, suffix=".test"
        )
        temp_file.close()

        file_size = size_gb * 1024 * 1024 * 1024
        with open(temp_file.name, "wb") as f:
            f.seek(file_size - 1)
            f.write(b'\0')

        return temp_file.name

    def test_redis_flapping(self):
        """Simulate Redis flapping (rapid start/stop)"""
        scenario = "Redis Flapping"
        print(f"🔄 Testing {scenario}...")

        observations = []

        # Try to find and flap Redis container
        try:
            redis_containers = []
            docker_ps = subprocess.check_output(
                ["docker", "ps", "-a", "--format", "{{.Names}}"], text=True
            )
            for name in docker_ps.strip().split("\n"):
                if "redis" in name.lower():
                    redis_containers.append(name)

            if redis_containers:
                redis_container = redis_containers[0]

                # First check baseline health
                baseline_health = self._health_check()
                observations.append(f"Baseline health: {'OK' if baseline_health else 'NOT OK'}")

                # Flap Redis 3 times
                for i in range(3):
                    subprocess.run(["docker", "stop", redis_container], capture_output=True)
                    time.sleep(2)
                    subprocess.run(["docker", "start", redis_container], capture_output=True)
                    time.sleep(3)
                    observations.append(f"Flap {i+1} complete")

                # Check if system recovered
                time.sleep(5)
                recovery_health = self._health_check()

                if recovery_health:
                    self._log_scenario(scenario, "PASS", observations)
                    print("✅ System recovered from Redis flapping")
                else:
                    self._log_scenario(scenario, "FAIL", observations)
                    print("❌ System failed to recover from Redis flapping")
            else:
                self._log_scenario(scenario, "SKIP", ["Redis container not detected in docker"])
                print("ℹ️  Redis container not found, skipping test")
        except Exception as e:
            self._log_scenario(scenario, "FAIL", [f"Error: {str(e)}"])
            print(f"❌ {scenario} test failed: {e}")

    def test_database_corruption(self):
        """Simulate database corruption by modifying files"""
        scenario = "Database Corruption"
        print(f"💾 Testing {scenario}...")

        observations = []

        # Look for database files in containers
        try:
            # Check if we have mnemosyne data directory
            mnemosyne_dir = Path("data/memory")
            if mnemosyne_dir.exists() and any(mnemosyne_dir.iterdir()):
                # Create backup of original data
                temp_backup = Path(tempfile.mkdtemp(prefix="mnemosyne_backup_"))
                shutil.copytree(mnemosyne_dir, temp_backup, dirs_exist_ok=True)

                observations.append("Mnemosyne data directory found")

                # Check baseline health
                baseline_health = self._health_check()
                observations.append(f"Baseline health: {'OK' if baseline_health else 'NOT OK'}")

                # Corrupt some database files
                db_files = list(mnemosyne_dir.rglob("*.db")) + list(mnemosyne_dir.rglob("*.sqlite"))
                for db_file in db_files:
                    try:
                        with open(db_file, "ab") as f:
                            f.write(b"\x00" * 1024)  # Add garbage to file
                        observations.append(f"Corrupted file: {db_file}")
                    except Exception:
                        continue

                time.sleep(10)

                # Check if system detects corruption and recovers
                recovery_health = self._health_check()
                observations.append(f"Recovery health: {'OK' if recovery_health else 'NOT OK'}")

                if recovery_health:
                    self._log_scenario(scenario, "PASS", observations)
                    print("✅ System recovered from database corruption")
                else:
                    self._log_scenario(scenario, "FAIL", observations)
                    print("❌ System failed to recover from database corruption")

                # Restore original data
                shutil.rmtree(mnemosyne_dir)
                shutil.copytree(temp_backup, mnemosyne_dir)
            else:
                self._log_scenario(scenario, "SKIP", ["Mnemosyne data directory not found"])
                print("ℹ️  Mnemosyne data not found, skipping test")
        except Exception as e:
            self._log_scenario(scenario, "FAIL", [f"Error: {str(e)}"])
            print(f"❌ {scenario} test failed: {e}")

    def test_disk_full(self):
        """Simulate disk full scenario by filling disk space"""
        scenario = "Disk Full"
        print(f"💿 Testing {scenario}...")

        observations = []

        try:
            disk_stats = shutil.disk_usage("/")
            available_gb = disk_stats.free / (1024 * 1024 * 1024)

            if available_gb > 2:
                # Create large files to fill disk space
                file_paths = []
                while available_gb > 1:
                    try:
                        file_path = self._create_large_file(1)
                        file_paths.append(file_path)
                        disk_stats = shutil.disk_usage("/")
                        available_gb = disk_stats.free / (1024 * 1024 * 1024)
                        observations.append(f"Created large file: {file_path}")
                    except Exception as e:
                        observations.append(f"Error creating large file: {e}")
                        break

                # Check system behavior when disk is almost full
                time.sleep(10)

                recovery_health = self._health_check()
                observations.append(f"Recovery health: {'OK' if recovery_health else 'NOT OK'}")

                if recovery_health:
                    self._log_scenario(scenario, "PASS", observations)
                    print("✅ System handled disk full scenario")
                else:
                    self._log_scenario(scenario, "FAIL", observations)
                    print("❌ System failed disk full scenario")

                # Clean up
                for file_path in file_paths:
                    try:
                        os.unlink(file_path)
                    except Exception:
                        pass
            else:
                self._log_scenario(scenario, "SKIP", [f"Insufficient disk space available: {available_gb:.1f} GB"])
                print(f"ℹ️  Insufficient disk space, skipping test")
        except Exception as e:
            self._log_scenario(scenario, "FAIL", [f"Error: {str(e)}"])
            print(f"❌ {scenario} test failed: {e}")

    def test_network_blackhole(self):
        """Simulate network blackhole by blocking external connections"""
        scenario = "Network Blackhole"
        print(f"🌐 Testing {scenario}...")

        observations = []

        try:
            # First record baseline health
            baseline_health = self._health_check()
            observations.append(f"Baseline health: {'OK' if baseline_health else 'NOT OK'}")

            # Try to block external connections
            if "iptables" in shutil.which("iptables"):
                # Block outgoing HTTP/HTTPS
                subprocess.run(
                    ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "80", "-j", "DROP"],
                    capture_output=True
                )
                subprocess.run(
                    ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "443", "-j", "DROP"],
                    capture_output=True
                )

                time.sleep(10)

                recovery_health = self._health_check()
                observations.append(f"Blackhole health: {'OK' if recovery_health else 'NOT OK'}")

                # Restore connectivity
                subprocess.run(
                    ["iptables", "-D", "OUTPUT", "-p", "tcp", "--dport", "80", "-j", "DROP"],
                    capture_output=True
                )
                subprocess.run(
                    ["iptables", "-D", "OUTPUT", "-p", "tcp", "--dport", "443", "-j", "DROP"],
                    capture_output=True
                )

                time.sleep(5)
                final_health = self._health_check()
                observations.append(f"Recovery health: {'OK' if final_health else 'NOT OK'}")

                if final_health:
                    self._log_scenario(scenario, "PASS", observations)
                    print("✅ System recovered from network blackhole")
                else:
                    self._log_scenario(scenario, "FAIL", observations)
                    print("❌ System failed to recover from network blackhole")
            else:
                self._log_scenario(scenario, "SKIP", ["iptables not available"])
                print("ℹ️  iptables not available, skipping test")
        except Exception as e:
            self._log_scenario(scenario, "FAIL", [f"Error: {str(e)}"])
            print(f"❌ {scenario} test failed: {e}")

    def test_clock_skew(self):
        """Simulate clock skew"""
        scenario = "Clock Skew"
        print(f"⏰ Testing {scenario}...")

        observations = []

        try:
            # Get initial system time
            initial_time = time.time()

            # Try to simulate time change
            # Note: On macOS, this requires special permissions
            if os.uname().sysname == "Darwin":
                # On macOS, we use "date" command to change time temporarily
                new_time = time.strftime("%m%d%H%M%Y.%S", time.gmtime(initial_time - 3600))
                subprocess.run(["sudo", "date", new_time], capture_output=True)
            else:
                # On Linux, we can use timedatectl
                subprocess.run(
                    ["sudo", "timedatectl", "set-time", time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(initial_time - 3600))],
                    capture_output=True
                )

            time.sleep(5)

            # Check if system handles clock skew
            recovery_health = self._health_check()
            observations.append(f"Clock skew health: {'OK' if recovery_health else 'NOT OK'}")

            # Reset to correct time from NTP
            if os.uname().sysname == "Darwin":
                subprocess.run(["sudo", "ntpdate", "time.apple.com"], capture_output=True)
            else:
                subprocess.run(["sudo", "timedatectl", "set-ntp", "true"], capture_output=True)

            time.sleep(5)
            final_health = self._health_check()
            observations.append(f"Recovery health: {'OK' if final_health else 'NOT OK'}")

            if final_health:
                self._log_scenario(scenario, "PASS", observations)
                print("✅ System handled clock skew")
            else:
                self._log_scenario(scenario, "FAIL", observations)
                print("❌ System failed clock skew scenario")
        except Exception as e:
            self._log_scenario(scenario, "SKIP", [f"Error: {str(e)}"])
            print(f"ℹ️  Clock skew test skipped: {e}")

    def generate_report(self):
        """Generate markdown report"""
        report_file = self.chaos_dir / "infra_resilience_report.md"

        report_content = f"""# Infrastructure Resilience Report
**Generated:** {self.report_data['timestamp']}  
**Version:** {self.report_data['version']}  
**Overall Status:** {self.report_data['overall_status']}

## Test Scenarios

"""

        for scenario in self.report_data["scenarios"]:
            status_icon = "✅" if scenario["status"] == "PASS" else \
                        "❌" if scenario["status"] == "FAIL" else "ℹ️"

            report_content += f"## {status_icon} {scenario['scenario']}\n"
            report_content += f"**Status:** {scenario['status']}\n\n"
            report_content += "### Observations:\n"
            for obs in scenario["observations"]:
                report_content += f"- {obs}\n"
            report_content += "\n"

        report_content += """
## Summary of Resilience

1. **System Degradation:**
   - Did the system degrade gracefully?
   - Which services failed and how?

2. **Isolation Mechanisms:**
   - Were problematic components isolated?
   - Did failures propagate to other services?

3. **Data Loss:**
   - Was there any data loss?
   - Did recovery restore data?

4. **Recovery Behavior:**
   - Did services automatically recover?
   - What manual intervention was required?

## Recommendations

Based on the test results, these improvements could enhance resilience:

1. **Redis Flapping:** Improve connection pooling and retry logic
2. **Database Corruption:** Enhance backup and recovery mechanisms
3. **Disk Full:** Implement better disk space monitoring and cleanup
4. **Network Blackhole:** Improve network partitioning detection
5. **Clock Skew:** Implement time synchronization monitoring
"""

        with open(report_file, "w") as f:
            f.write(report_content)

        print(f"📄 Report generated: {report_file}")


def main():
    print("🚀 Starting Infrastructure Chaos Simulation...")
    print(f"📊 Target System: IPPOC v1.0.2")
    print()

    simulator = ChaosSimulator()

    # Test scenarios
    simulator.test_redis_flapping()
    simulator.test_database_corruption()
    simulator.test_disk_full()
    simulator.test_network_blackhole()
    simulator.test_clock_skew()

    # Generate report
    simulator.generate_report()

    print()
    print("🏁 Chaos simulation complete!")


if __name__ == "__main__":
    main()
