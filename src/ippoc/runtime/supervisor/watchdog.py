import subprocess
import os
import signal
import sys
import time
from pathlib import Path
import requests
from typing import Dict, Tuple

class ServiceManager:
    """
    The Organ Supervisor (OSC-01 / PID-1).
    Responsible for the hierarchical metabolic health of IPPOC cognitive organs.
    """
    def __init__(self, ippoc_home: Path):
        self.ippoc_home = ippoc_home
        self.processes: Dict[str, subprocess.Popen] = {}
        self.restart_counts: Dict[str, int] = {}
        self.is_shutting_down = False

    def _wait_for_health(self, name: str, url: str, timeout: int = 30):
        """Wait for a service to become healthy."""
        print(f"⌛ Waiting for {name} health check ({url})...", end="", flush=True)
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = requests.get(url, timeout=2)
                if resp.status_code == 200:
                    print(" ✅")
                    return True
            except Exception:
                pass
            print(".", end="", flush=True)
            time.sleep(2)
        print(" ❌ Timeout")
        return False

    def start_soma(self, db_type="sqlite"):
        if self.is_shutting_down: return
        print(f"📦 [OSC-01] Starting Soma (Identity & Trust)...")
        
        # Start Python-based Soma service (pure Python implementation)
        soma_server_path = Path(__file__).parent.parent.parent / "soma" / "server.py"
        
        if not soma_server_path.exists():
            print("\n🔴 [OSC-01] SOMA NOT AVAILABLE")
            print("==================================")
            print("Running in BRAIN-ONLY MODE")
            print("Identity & Trust services DISABLED")
            print("Capabilities:")
            print("  - Cognition (Cortex only)")
            print("  - Tool execution (limited)")
            print("  - No trust mesh")
            print("  - No reputation system")
            print("  - No body verification")
            print("==================================")
            return

        env = os.environ.copy()
        env["IPPOC_HOME"] = str(self.ippoc_home)
        env["IPPOC_DATABASE_TYPE"] = db_type

        try:
            proc = subprocess.Popen(
                [sys.executable, str(soma_server_path)],
                env=env,
                stdout=sys.stdout, stderr=sys.stderr, text=True
            )
            self.processes["Soma"] = proc
            
            # Verify Soma health
            if not self._wait_for_health("Soma", "http://localhost:8081/v1/system/diagnostics"):
                print("⚠️  [OSC-01] Soma failed health check. Continuing in degraded mode (Brain-Only).")
                if proc.poll() is not None:
                     del self.processes["Soma"]
                # Explicitly disable auth when running in brain-only mode
                os.environ["IPPOC_AUTH_ENABLED"] = "false"
        except Exception as e:
            print(f"⚠️  [OSC-01] Failed to start Soma service: {e}")
            print("\n🔴 [OSC-01] SOMA NOT AVAILABLE")
            print("==================================")
            print("Running in BRAIN-ONLY MODE")
            print("Identity & Trust services DISABLED")
            print("Capabilities:")
            print("  - Cognition (Cortex only)")
            print("  - Tool execution (limited)")
            print("  - No trust mesh")
            print("  - No reputation system")
            print("  - No body verification")
            print("==================================")
            # Explicitly disable auth when running in brain-only mode
            os.environ["IPPOC_AUTH_ENABLED"] = "false"


    def start_cortex(self, redis_url=None):
        if self.is_shutting_down: return
        
        # Dependency Check: Soma must be alive
        if "Soma" not in self.processes or self.processes["Soma"].poll() is not None:
            print("⚠️  [OSC-01] Cortex starting without Soma (Brain-Only Mode). Identity & Trust services unavailable.")
            # Proceed anyway

        print(f"🧠 [OSC-01] Starting Cortex (Cognition & Tools)...")
        
        # Determine Cortex directory based on environment
        if os.getenv("IPPOC_PRODUCTION"):
            cortex_dir = self.ippoc_home / "bin"
        else:
            cortex_dir = Path(__file__).parent.parent.parent / "cortex"
        env = os.environ.copy()
        env["IPPOC_HOME"] = str(self.ippoc_home)
        if redis_url:
            env["IPPOC_REDIS_URL"] = redis_url
        else:
            env["IPPOC_USE_INTERNAL_QUEUE"] = "true"

        # Use the same python interpreter that launched this process to ensure venv/dependencies are inherited
        # RC FIX: Launch as a module to preserve package structure and imports
        # RC FIX: Explicitly forward API Key if present
        if "IPPOC_API_KEY" in os.environ:
            env["IPPOC_API_KEY"] = os.environ["IPPOC_API_KEY"]

        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = str(cortex_dir.parent) + os.pathsep + env["PYTHONPATH"]
        else:
            env["PYTHONPATH"] = str(cortex_dir.parent)

        proc = subprocess.Popen(
            [sys.executable, "-m", "cortex.cortex.server"],
            env=env,
            cwd=str(cortex_dir.parent),
            stdout=sys.stdout, stderr=sys.stderr, text=True
        )
        self.processes["Cortex"] = proc
        
        # Verify Cortex health
        if not self._wait_for_health("Cortex", "http://localhost:8000/readyz"):
            print("⚠️ Cortex failed readiness probe.")

    def monitor(self, db_type="sqlite", redis_url=None):
        """Watcher loop representing the Metabolic Monitor."""
        try:
            while not self.is_shutting_down:
                for name in list(self.processes.keys()):
                    proc = self.processes[name]
                    status = proc.poll()
                    if status is not None:
                        print(f"🔥 [OSC-01] {name} terminated with exit code {status}")
                        self.shutdown()
                        return
                time.sleep(2)
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        self.is_shutting_down = True
        print("\n🛑 [OSC-01] Intentional Shutdown Proceeding...")
        # Shutdown order: Cortex first, then Soma
        for name in ["Cortex", "Soma"]:
            if name in self.processes:
                proc = self.processes[name]
                print(f"   Terminating {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except Exception:
                    proc.kill()
        print("✅ IPPOC Metropolis Offline.")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) > 1:
        ippoc_home = Path(sys.argv[1])
    else:
        # Default to current directory
        ippoc_home = Path(".")
    
    try:
        manager = ServiceManager(ippoc_home)
        manager.start_soma()
        manager.start_cortex()
        manager.monitor()
    except Exception as e:
        print(f"❌ [OSC-01] Fatal error: {e}")
        sys.exit(1)