#!/usr/bin/env python3
"""
IPPOC CLI - Intelligent Personal Processing & Orchestration Core
Main entry point for the complete system with all services.
"""
import os
import sys
import time
import signal
import socket
import argparse
import subprocess
import logging
import json
from pathlib import Path
from typing import Optional, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("IPPOC.CLI")

# ============================================================================
# SERVICE CONFIGURATION
# ============================================================================

# Service Ports
SOMA_PORT = 8081          # Rust-based Soma (Identity + Mesh + Economy)
SOMA_GRPC_PORT = 9081     # gRPC service
CORTEX_PORT = 8000        # Cortex (Cognition & Tools)
BODY_PORT = 8002          # Body (placeholder for execution)
MEMORY_PORT = 8003        # Memory/Mnemosyne (optional)
ECONOMY_PORT = 8004       # Economy (placeholder)

# Instance Configuration
INSTANCE_ROOT = os.path.expanduser("~/.ippoc/instances/main")
INSTANCE_DATA = os.path.join(INSTANCE_ROOT, "data")
INSTANCE_STATE = os.path.join(INSTANCE_ROOT, "state")
PID_DIR = os.path.join(INSTANCE_ROOT, "pids")

# ============================================================================
# SERVICE MANAGEMENT
# ============================================================================

def ensure_instance_dirs():
    """Create instance directories if they don't exist."""
    for d in [INSTANCE_ROOT, INSTANCE_DATA, INSTANCE_STATE, PID_DIR]:
        os.makedirs(d, exist_ok=True)
    logger.info(f"🦞 IPPOC Instance Root: {INSTANCE_ROOT}")

def check_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(('localhost', port))
            return True
        except ConnectionRefusedError:
            return False
        except Exception:
            return False

def get_pid_path(service: str) -> str:
    """Get the PID file path for a service."""
    return os.path.join(PID_DIR, f"{service}.pid")

def save_pid(service: str, pid: int):
    """Save PID to file."""
    pid_file = get_pid_path(service)
    os.makedirs(os.path.dirname(pid_file), exist_ok=True)
    with open(pid_file, 'w') as f:
        f.write(str(pid))
    logger.debug(f"Saved PID {pid} for {service}")

def load_pid(service: str) -> Optional[int]:
    """Load PID from file."""
    pid_file = get_pid_path(service)
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            return int(f.read().strip())
    return None

def is_process_running(pid: int) -> bool:
    """Check if a process is running."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False

def cleanup_stale_pid(service: str):
    """Remove stale PID file if process is not running."""
    pid = load_pid(service)
    if pid and not is_process_running(pid):
        pid_file = get_pid_path(service)
        if os.path.exists(pid_file):
            os.remove(pid_file)
        logger.debug(f"Cleaned up stale PID for {service}")

def wait_for_url(url: str, timeout: float = 30.0, interval: float = 0.5) -> bool:
    """Wait for a URL to become available."""
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(interval)
    return False

def kill_process_on_port(port: int):
    """Kill any process using a specific port."""
    try:
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    logger.info(f"Killed process {pid} on port {port}")
                except (ValueError, ProcessLookupError):
                    pass
            time.sleep(1)
    except FileNotFoundError:
        pass

# ============================================================================
# SERVICE STARTUP
# ============================================================================

def start_soma() -> Optional[subprocess.Popen]:
    """
    Start Soma - Identity & Trust Service (Rust-based)
    
    Provides:
    - Identity registration and trust management
    - Mesh/Nervous System networking
    - Economy (wallet, balances, reputation)
    - Lifecycle management
    - Resource allocation
    - Sovereign vault
    """
    logger.info(f"📦 [SOMA] Starting Identity & Trust Service (port {SOMA_PORT})...")
    
    if check_port_in_use(SOMA_PORT):
        logger.info(f"  Soma already running on port {SOMA_PORT}")
        return None
    
    kill_process_on_port(SOMA_PORT)
    
    soma_src = os.path.join(INSTANCE_ROOT, "..", "..", "src", "ippoc", "soma")
    soma_cargo = os.path.join(soma_src, "Cargo.toml")
    
    if os.path.exists(soma_cargo):
        logger.info("  Building Soma (Rust)...")
        try:
            subprocess.run(
                ['cargo', 'build', '--release'],
                cwd=soma_src,
                capture_output=True,
                timeout=300
            )
        except Exception as e:
            logger.warning(f"  Build failed or cargo not available: {e}")
    
    soma_env = os.environ.copy()
    soma_env["IPPOC_INSTANCE"] = "main"
    soma_env["IPPOC_DATA_DIR"] = INSTANCE_DATA
    soma_env["IPPOC_HOME"] = INSTANCE_ROOT
    
    soma_bin = os.path.join(soma_src, "target", "release", "ippoc-soma")
    if not os.path.exists(soma_bin):
        soma_bin = os.path.join(soma_src, "target", "debug", "ippoc-soma")
    
    if os.path.exists(soma_bin):
        cmd = [soma_bin, "--port", str(SOMA_PORT)]
    else:
        soma_py = os.path.join(soma_src, "server.py")
        if os.path.exists(soma_py):
            cmd = [sys.executable, soma_py]
        else:
            logger.error("  No Soma binary or server.py found")
            return None
    
    proc = subprocess.Popen(
        cmd,
        env=soma_env,
        cwd=soma_src
    )
    
    save_pid("soma", proc.pid)
    logger.info(f"  ✅ Soma started (PID: {proc.pid})")
    return proc

def start_cortex(api_key: str) -> Optional[subprocess.Popen]:
    """
    Start Cortex - Cognition & Tools Service
    """
    logger.info(f"🧠 [CORTEX] Starting Cognition Service (port {CORTEX_PORT})...")
    
    if check_port_in_use(CORTEX_PORT):
        logger.info(f"  Cortex already running on port {CORTEX_PORT}")
        return None
    
    kill_process_on_port(CORTEX_PORT)
    
    cortex_env = os.environ.copy()
    cortex_env["IPPOC_INSTANCE"] = "main"
    cortex_env["IPPOC_API_KEY"] = api_key
    cortex_env["IPPOC_SOMA_URL"] = f"http://localhost:{SOMA_PORT}"
    cortex_env["IPPOC_HOME"] = INSTANCE_ROOT
    cortex_env["IPPOC_DATA_DIR"] = INSTANCE_DATA
    cortex_env["DEV_MODE"] = "true"
    cortex_env["IPPOC_LOG_LEVEL"] = "INFO"
    
    cortex_py = os.path.join(INSTANCE_ROOT, "..", "..", "src", "cortex", "server.py")
    if not os.path.exists(cortex_py):
        cortex_py = os.path.join(INSTANCE_ROOT, "..", "..", "src", "ippoc", "cortex", "server.py")
    
    if not os.path.exists(cortex_py):
        logger.error("  Cortex server.py not found")
        return None
    
    cmd = [sys.executable, cortex_py]
    
    proc = subprocess.Popen(
        cmd,
        env=cortex_env,
        cwd=os.path.dirname(cortex_py) or INSTANCE_ROOT
    )
    
    save_pid("cortex", proc.pid)
    logger.info(f"  ✅ Cortex started (PID: {proc.pid})")
    return proc

def start_body() -> Optional[subprocess.Popen]:
    """
    Start Body - Execution Service (port 8002)
    """
    logger.info(f"🤖 [BODY] Starting Execution Service (port {BODY_PORT})...")
    
    if check_port_in_use(BODY_PORT):
        logger.info(f"  Body already running on port {BODY_PORT}")
        return None
    
    kill_process_on_port(BODY_PORT)
    
    body_env = os.environ.copy()
    body_env["IPPOC_INSTANCE"] = "main"
    body_env["IPPOC_SOMA_URL"] = f"http://localhost:{SOMA_PORT}"
    
    body_py = os.path.join(INSTANCE_DATA, "body_placeholder.py")
    with open(body_py, 'w') as f:
        f.write('''#!/usr/bin/env python3
import http.server
import socketserver
import json

PORT = 8002
DATA_DIR = os.path.expanduser("~/.ippoc/instances/main/data")

class BodyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "alive"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == "/v1/execute":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "executed", "output": "Body service active"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    import os
    os.makedirs(DATA_DIR, exist_ok=True)
    with socketserver.TCServer(("localhost", PORT), BodyHandler) as httpd:
        print(f"Body service ready on port {PORT}")
        httpd.serve_forever()
''')
    
    cmd = [sys.executable, body_py]
    
    proc = subprocess.Popen(cmd, env=body_env)
    save_pid("body", proc.pid)
    logger.info(f"  ✅ Body started (PID: {proc.pid})")
    return proc

def start_economy() -> Optional[subprocess.Popen]:
    """
    Start Economy Service (port 8004)
    """
    logger.info(f"💰 [ECONOMY] Starting Economy Service (port {ECONOMY_PORT})...")
    
    if check_port_in_use(ECONOMY_PORT):
        logger.info(f"  Economy already running on port {ECONOMY_PORT}")
        return None
    
    kill_process_on_port(ECONOMY_PORT)
    
    try:
        import urllib.request
        url = f"http://localhost:{SOMA_PORT}/v1/economy/balance"
        urllib.request.urlopen(url, timeout=2)
        logger.info(f"  ✅ Economy available via Soma (port {SOMA_PORT})")
        return None
    except Exception:
        pass
    
    economy_py = os.path.join(INSTANCE_DATA, "economy_service.py")
    with open(economy_py, 'w') as f:
        f.write('''#!/usr/bin/env python3
"""Economy Service - Token and Budget Management"""
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

DATA_DIR = os.path.expanduser("~/.ippoc/instances/main/data")
BALANCE_FILE = os.path.join(DATA_DIR, "economy.json")

class EconomyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        if self.path == "/v1/economy/balance":
            balance = {"tokens": 10000, "budget": 1000, "reputation": 100}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(balance).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == "/v1/economy/transfer":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    server = HTTPServer(("localhost", 8004), EconomyHandler)
    print("Economy service ready on port 8004")
    server.serve_forever()
''')
    
    proc = subprocess.Popen([sys.executable, economy_py])
    save_pid("economy", proc.pid)
    logger.info(f"  ✅ Economy started (PID: {proc.pid})")
    return proc

# ============================================================================
# API KEY MANAGEMENT
# ============================================================================

def issue_api_key() -> Optional[str]:
    """Issue an API key from Soma."""
    import urllib.request
    import json
    
    url = f"http://localhost:{SOMA_PORT}/v1/auth/issue"
    try:
        req = urllib.request.Request(url, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            api_key = data.get("api_key")
            logger.info(f"  ✅ API key issued: {api_key[:8]}...")
            return api_key
    except Exception as e:
        logger.error(f"  ❌ Failed to issue API key: {e}")
        return None

def verify_api_key(api_key: str) -> bool:
    """Verify an API key with Soma."""
    import urllib.request
    import json
    
    url = f"http://localhost:{SOMA_PORT}/v1/auth/verify?api_key={api_key}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("status") == "valid"
    except Exception:
        return False

# ============================================================================
# SERVICE DISCOVERY
# ============================================================================

def get_all_services_status() -> Dict[str, dict]:
    """Get status of all IPPOC services."""
    services = {}
    
    for name, port, url in [
        ("soma", SOMA_PORT, f"http://localhost:{SOMA_PORT}/health"),
        ("cortex", CORTEX_PORT, f"http://localhost:{CORTEX_PORT}/readyz"),
        ("body", BODY_PORT, f"http://localhost:{BODY_PORT}/health"),
        ("economy", ECONOMY_PORT, f"http://localhost:{ECONOMY_PORT}/v1/economy/balance"),
    ]:
        pid = load_pid(name)
        running = check_port_in_use(port)
        healthy = False
        
        if running:
            try:
                import urllib.request
                urllib.request.urlopen(url, timeout=2)
                healthy = True
            except Exception:
                pass
        
        services[name] = {
            "port": port,
            "pid": pid,
            "running": running,
            "healthy": healthy
        }
    
    return services

def print_services_status():
    """Print status of all services."""
    print("\n" + "="*60)
    print("📊 IPPOC Services Status")
    print("="*60)
    
    services = get_all_services_status()
    
    for name, info in services.items():
        status = "🟢 Running" if info["running"] else "🔴 Stopped"
        healthy = "✓" if info["healthy"] else "✗"
        pid = f" (PID: {info['pid']})" if info["pid"] else ""
        port = f":{info['port']}"
        
        print(f"  {name.upper():8} {status}{pid} port{port} healthy={healthy}")
    
    print("="*60 + "\n")

# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

def run_services():
    """Start all IPPOC services in correct order."""
    ensure_instance_dirs()
    
    for service in ["soma", "cortex", "body", "economy"]:
        cleanup_stale_pid(service)
    
    processes = []
    
    logger.info("🚀 Starting IPPOC - Full Stack Integration")
    logger.info("="*60)
    
    # Phase 1: Infrastructure (Soma)
    soma_proc = start_soma()
    if soma_proc:
        processes.append(("soma", soma_proc))
    
    soma_health = f"http://localhost:{SOMA_PORT}/health"
    logger.info(f"  ⏳ Waiting for Soma ({soma_health})...")
    if wait_for_url(soma_health, timeout=20):
        logger.info("  ✅ Soma ready")
    else:
        logger.warning("  ⚠️ Soma health check timed out")
    
    # Get API Key
    api_key = issue_api_key()
    if not api_key:
        logger.error("❌ Failed to issue API key - continuing anyway")
    
    # Phase 2: Execution Services
    body_proc = start_body()
    if body_proc:
        processes.append(("body", body_proc))
    
    economy_proc = start_economy()
    if economy_proc:
        processes.append(("economy", economy_proc))
    
    # Phase 3: Cognitive Services
    cortex_proc = start_cortex(api_key if api_key else "")
    if cortex_proc:
        processes.append(("cortex", cortex_proc))
    
    cortex_health = f"http://localhost:{CORTEX_PORT}/readyz"
    logger.info(f"  ⏳ Waiting for Cortex ({cortex_health})...")
    if wait_for_url(cortex_health, timeout=30):
        logger.info("  ✅ Cortex ready")
    else:
        logger.warning("  ⚠️ Cortex health check timed out")
    
    print_services_status()
    
    logger.info("🎉 All services started!")
    logger.info("="*60)
    
    print("📝 Service Endpoints:")
    print(f"   Soma (Identity + Mesh + Economy): http://localhost:{SOMA_PORT}")
    print(f"   Cortex (Cognition):               http://localhost:{CORTEX_PORT}")
    print(f"   Body (Execution):                 http://localhost:{BODY_PORT}")
    print(f"   Economy:                          http://localhost:{ECONOMY_PORT}")
    print()
    
    try:
        for name, proc in processes:
            if proc and proc.poll() is None:
                proc.wait()
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down...")
        stop_all()
    
    return True

def stop_all():
    """Stop all IPPOC services."""
    logger.info("🛑 Stopping all services...")
    
    for service in ["cortex", "economy", "body", "soma"]:
        pid = load_pid(service)
        if pid and is_process_running(pid):
            try:
                os.kill(pid, signal.SIGTERM)
                logger.info(f"  Stopped {service} (PID: {pid})")
            except ProcessLookupError:
                pass
        pid_file = get_pid_path(service)
        if os.path.exists(pid_file):
            os.remove(pid_file)
    
    for port in [CORTEX_PORT, ECONOMY_PORT, BODY_PORT, SOMA_PORT]:
        kill_process_on_port(port)

# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="IPPOC - Intelligent Personal Processing & Orchestration Core",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
 ippoc run              Start all services
 ippoc status           Show service status
 ippoc stop             Stop all services
        """
    )
    parser.add_argument("command", choices=["run", "status", "stop"], default="run", help="Command to execute")
    parser.add_argument("--dev", action="store_true", help="Development mode")
    
    args = parser.parse_args()
    
    if args.dev:
        os.environ["DEV_MODE"] = "true"
    
    if args.command == "run":
        run_services()
    elif args.command == "status":
        print_services_status()
    elif args.command == "stop":
        stop_all()

if __name__ == "__main__":
    main()
