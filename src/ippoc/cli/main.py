import argparse
import sys
import os
import json
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any

CORTEX_URL = os.getenv("CORTEX_URL", "http://localhost:8000")
SOMA_URL = os.getenv("SOMA_URL", "http://localhost:8081")

class IppocClient:
    def __init__(self, api_key: Optional[str] = None):
        # Lazy initialization - don't connect to anything on import
        self.api_key = api_key
        self.session = None

    def _init_session(self):
        if self.session is None:
            self.session = requests.Session()
            if self.api_key is None:
                try:
                    from ippoc.runtime.bootstrap.auth import get_api_key
                    self.api_key = get_api_key()
                except Exception as e:
                    print(f"⚠️ Failed to get API key: {e}")
                    # Continue without API key for read-only operations
            if self.api_key:
                self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def _handle_response(self, response: requests.Response):
        if response.status_code >= 400:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None
        return response.json()

    def _is_service_running(self, url: str, timeout: float = 2.0) -> bool:
        """Check if a service is running and responding to HTTP requests"""
        try:
            resp = requests.get(url, timeout=timeout)
            return resp.status_code == 200
        except Exception:
            return False

    def ensure_services_ready(self, timeout: int = 30) -> bool:
        """Ensure both Soma and Cortex services are running and ready"""
        # Check both services are running
        soma_ready = self._is_service_running(f"{SOMA_URL}/v1/system/diagnostics")
        cortex_ready = self._is_service_running(f"{CORTEX_URL}/healthz")
        
        if not soma_ready or not cortex_ready:
            print("❌ IPPOC core services not running. Start with: ippoc run")
            return False
        
        return True

    def ingest_signal(self, signal_type: str, content: str, source: str = "cli"):
        if not self.ensure_services_ready():
            return None
        
        if self.session is None:
            self._init_session()
        
        payload = {
            "type": signal_type.upper(),
            "content": content,
            "source": source,
            "timestamp": time.time(),
            "confidence": 1.0
        }
        
        try:
            resp = self.session.post(f"{CORTEX_URL}/v1/signals/ingest", json=payload, timeout=10)
            return self._handle_response(resp)
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed. Services may be down.")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def get_status(self):
        if self.session is None:
            self._init_session()
        
        try:
            resp = self.session.get(f"{CORTEX_URL}/health", timeout=2)
            return self._handle_response(resp)
        except requests.exceptions.ConnectionError:
            print("❌ IPPOC core not running. Try: ippoc run")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def list_intents(self):
        if not self.ensure_services_ready():
            return {"intents": []}
        
        if self.session is None:
            self._init_session()
        
        try:
            resp = self.session.get(f"{CORTEX_URL}/v1/intents/list", timeout=10)
            result = self._handle_response(resp) or {"intents": []}
            
            # Ensure intents is always an iterable and contains valid entries
            if "intents" not in result or not isinstance(result["intents"], list):
                result["intents"] = []
            
            # Clean up any invalid intent entries
            cleaned_intents = []
            for intent in result["intents"]:
                if isinstance(intent, dict):
                    # Ensure required fields exist and are valid
                    if all(key in intent for key in ["priority", "description", "intent_type"]):
                        # Handle possible None values
                        intent["priority"] = intent["priority"] or 0.0
                        intent["description"] = intent["description"] or "Unknown"
                        intent["intent_type"] = intent["intent_type"] or "Unknown"
                        cleaned_intents.append(intent)
            
            result["intents"] = cleaned_intents
            return result
            
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed. Services may be down.")
            return {"intents": []}
        except Exception as e:
            print(f"❌ Error: {e}")
            return {"intents": []}

    def stream_thoughts(self):
        if not self.ensure_services_ready():
            return
        
        if self.session is None:
            self._init_session()
        
        # SSE stream handled via raw requests to keep it simple
        from requests.exceptions import ChunkedEncodingError
        try:
            with self.session.get(f"{CORTEX_URL}/v1/cognitive/stream", stream=True, timeout=30) as resp:
                if resp.status_code != 200:
                    print(f"❌ Failed to connect: {resp.status_code}")
                    return
                print("🧠 Streaming IPPOC Thoughts (Ctrl+C to stop)...")
                for line in resp.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        if decoded.startswith("data: "):
                            try:
                                data = json.loads(decoded[6:])
                                timestamp = time.strftime('%H:%M:%S', time.localtime(data.get('timestamp', time.time())))
                                level = data.get('level', 'thought').upper()
                                content = data.get('content', '')
                                print(f"[{timestamp}] {level}: {content}")
                            except json.JSONDecodeError:
                                pass
        except KeyboardInterrupt:
            print("\n👋 Stream stopped.")
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed. Services may be down.")
        except Exception as e:
            print(f"❌ Error: {e}")

    def explain(self, execution_id: str):
        if not self.ensure_services_ready():
            return None
        
        if self.session is None:
            self._init_session()
        
        url = f"{CORTEX_URL}/v1/orchestrator/explain/{execution_id}"
        if execution_id == "latest":
            url = f"{CORTEX_URL}/v1/orchestrator/explain/latest"
        
        try:
            resp = self.session.get(url, timeout=10)
            return self._handle_response(resp)
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed. Services may be down.")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def get_violations(self, limit: int = 10):
        if not self.ensure_services_ready():
            return {"security_violations": [], "canon_violations": []}
        
        if self.session is None:
            self._init_session()
        
        try:
            resp = self.session.get(f"{CORTEX_URL}/v1/system/violations", params={"limit": limit}, timeout=10)
            return self._handle_response(resp) or {"security_violations": [], "canon_violations": []}
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed. Services may be down.")
            return {"security_violations": [], "canon_violations": []}
        except Exception as e:
            print(f"❌ Error: {e}")
            return {"security_violations": [], "canon_violations": []}

    def control_autonomy(self, action: str):
        if not self.ensure_services_ready():
            return None
        
        if self.session is None:
            self._init_session()
        
        try:
            resp = self.session.post(f"{CORTEX_URL}/v1/system/autonomy/control", params={"action": action}, timeout=10)
            return self._handle_response(resp)
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed. Services may be down.")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description="IPPOC Universal Platform CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Run Command
    run_parser = subparsers.add_parser("run", help="Start IPPOC services")
    run_parser.add_argument("instance", nargs="?", default="main", help="Instance name (default: main)")
    run_parser.add_argument("--db", choices=["sqlite", "postgres"], default="sqlite", help="Database engine (default: sqlite)")
    run_parser.add_argument("--redis", help="Redis URL (optional, uses internal queue if missing)")

    # Setup Command
    setup_parser = subparsers.add_parser("setup", help="Verify and configure IPPOC environment")
    setup_parser.add_argument("instance", nargs="?", default="main", help="Instance name (default: main)")

    # Signal Command
    signal_parser = subparsers.add_parser("signal", help="Signal operations")
    signal_sub = signal_parser.add_subparsers(dest="subcommand")
    ingest_parser = signal_sub.add_parser("ingest", help="Ingest a sensory signal")
    ingest_parser.add_argument("type", choices=["SIGHT", "HEARING", "TOUCH", "SMELL", "TASTE"], help="Signal type")
    ingest_parser.add_argument("content", help="Signal content/message")

    # Status Command
    subparsers.add_parser("status", help="Get IPPOC system status")

    # Intent Command
    subparsers.add_parser("intents", help="List active cognitive intents")

    # Thought Command
    thought_parser = subparsers.add_parser("thoughts", help="Cognitive thought stream")
    thought_parser.add_argument("--tail", action="store_true", help="Follow the thought stream")

    # Explain Command
    explain_parser = subparsers.add_parser("explain", help="Explain specific execution or intent")
    explain_parser.add_argument("id", nargs="?", default="latest", help="Execution ID or 'latest'")

    # Violations Command
    subparsers.add_parser("violations", help="List security and canon violations")

    # Autonomy Command
    autonomy_parser = subparsers.add_parser("autonomy", help="Control IPPOC autonomy")
    autonomy_parser.add_argument("action", choices=["on", "off", "pause"], help="Action to perform")

    args = parser.parse_args()

    # Client-based commands
    client = IppocClient()

    if args.command == "signal":
        if args.subcommand == "ingest":
            result = client.ingest_signal(args.type, args.content)
            if result:
                print(f"✅ Signal ingested. Cognitive status: {result.get('status')}")

    elif args.command == "status":
        result = client.get_status()
        if result:
            print(json.dumps(result, indent=2))

    elif args.command == "intents":
        result = client.list_intents()
        intents = result.get("intents", [])
        if not intents:
            print("∅ No active intents.")
        for i in intents:
            print(f"- [{i.get('priority'):.2f}] {i.get('description')} ({i.get('intent_type')})")

    elif args.command == "thoughts":
        client.stream_thoughts()

    elif args.command == "explain":
        result = client.explain(args.id)
        if result:
            print(json.dumps(result, indent=2))

    elif args.command == "violations":
        result = client.get_violations()
        if result:
            print("--- Security Violations (Ledger) ---")
            for v in result.get("security_violations", []):
                 print(f"ID: {v.get('execution_id')} | Tool: {v.get('tool_name')} | Error: {v.get('error_message')}")
            
            print("\n--- Canon Violations (Brain) ---")
            for v in result.get("canon_violations", []):
                 print(f"Time: {v.get('time')} | Action: {v.get('decision', {}).get('action')} | Reason: {v.get('decision', {}).get('reason')}")

    elif args.command == "autonomy":
        result = client.control_autonomy(args.action)
        if result:
            print(f"✅ {result.get('status')}")

    # Legacy-style commands
    elif args.command == "run":
        run_services(args)
    elif args.command == "setup":
        setup_env(args.instance)
    else:
        if not args.command:
            parser.print_help()

def setup_env(instance_name: str):
    ippoc_base = Path(os.getenv("IPPOC_BASE_DIR", Path.home() / ".ippoc"))
    instance_root = ippoc_base / "instances" / instance_name
    
    print(f"🦞 IPPOC Instance Root: {instance_root}")
    
    instance_root.mkdir(parents=True, exist_ok=True)
    (instance_root / "data").mkdir(exist_ok=True)
    (instance_root / "logs").mkdir(exist_ok=True)
    print(f"✅ Instance '{instance_name}' verified.")
    return instance_root

def is_port_in_use(port):
    """Check if a port is already in use."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_services(args):
    # Check if services are already running
    if is_port_in_use(8081) and is_port_in_use(8000):
        print("✅ Services are already running")
        return
    
    # Check individual ports
    if is_port_in_use(8081):
        print("❌ Soma is already running on port 8081")
        return
    
    if is_port_in_use(8000):
        print("❌ Cortex is already running on port 8000")
        return
        
    from ippoc.runtime.supervisor.watchdog import ServiceManager
    instance_root = setup_env(args.instance)
    manager = ServiceManager(instance_root)
    manager.start_soma(db_type=args.db)
    
    # Wait for Soma to start before attempting to get API key
    import time
    start_time = time.time()
    soma_healthy = False
    while time.time() - start_time < 30:
        try:
            import requests
            resp = requests.get(f"{SOMA_URL}/v1/system/diagnostics", timeout=2)
            if resp.status_code == 200:
                soma_healthy = True
                break
        except Exception:
            pass
        time.sleep(2)
    
    if soma_healthy:
        # Now that Soma is running, ensure API key is available
        if "IPPOC_API_KEY" not in os.environ:
            from ippoc.runtime.bootstrap.auth import get_api_key
            try:
                os.environ["IPPOC_API_KEY"] = get_api_key()
            except Exception as e:
                print(f"❌ Failed to get API key: {e}")
                manager.shutdown()
                return
    else:
        print("❌ Soma failed to start properly")
        manager.shutdown()
        return
    
    manager.start_cortex(redis_url=args.redis)
    manager.monitor(db_type=args.db, redis_url=args.redis)

if __name__ == "__main__":
    main()
