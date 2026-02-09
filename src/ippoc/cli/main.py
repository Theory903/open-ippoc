import argparse
import sys
import os
import json
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any

# --- Configuration ---
# --- Configuration ---
from ippoc.runtime.bootstrap.auth import get_api_key

CORTEX_URL = os.getenv("CORTEX_URL", "http://localhost:8001")
SOMA_URL = os.getenv("SOMA_URL", "http://localhost:8002")
API_KEY = get_api_key()

class IppocClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or API_KEY
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def _handle_response(self, response: requests.Response):
        if response.status_code >= 400:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None
        return response.json()

    def ingest_signal(self, signal_type: str, content: str, source: str = "cli"):
        payload = {
            "type": signal_type.upper(),
            "content": content,
            "source": source,
            "timestamp": time.time(),
            "confidence": 1.0
        }
        resp = self.session.post(f"{CORTEX_URL}/v1/signals/ingest", json=payload)
        return self._handle_response(resp)

    def get_status(self):
        try:
            resp = self.session.get(f"{CORTEX_URL}/health", timeout=1)
            return self._handle_response(resp)
        except requests.exceptions.ConnectionError:
            print("❌ IPPOC core not running. Try: ippoc run")
            return None

    def list_intents(self):
        resp = self.session.get(f"{CORTEX_URL}/v1/intents/list")
        return self._handle_response(resp)

    def stream_thoughts(self):
        # SSE stream handled via raw requests to keep it simple
        from requests.exceptions import ChunkedEncodingError
        try:
            with self.session.get(f"{CORTEX_URL}/v1/cognitive/stream", stream=True) as resp:
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

    def explain(self, execution_id: str):
        url = f"{CORTEX_URL}/v1/orchestrator/explain/{execution_id}"
        if execution_id == "latest":
            url = f"{CORTEX_URL}/v1/orchestrator/explain/latest"
        resp = self.session.get(url)
        return self._handle_response(resp)

    def get_violations(self, limit: int = 10):
        resp = self.session.get(f"{CORTEX_URL}/v1/system/violations", params={"limit": limit})
        return self._handle_response(resp)

    def control_autonomy(self, action: str):
        resp = self.session.post(f"{CORTEX_URL}/v1/system/autonomy/control", params={"action": action})
        return self._handle_response(resp)

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
        if result:
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

def run_services(args):
    # This import is here to avoid heavy dependencies for simple CLI commands
    # Ensure default key is set for subprocesses if not present
    if "IPPOC_API_KEY" not in os.environ:
        os.environ["IPPOC_API_KEY"] = get_api_key()
        
    from ippoc.runtime.supervisor.watchdog import ServiceManager
    instance_root = setup_env(args.instance)
    manager = ServiceManager(instance_root)
    manager.start_soma(db_type=args.db)
    manager.start_cortex(redis_url=args.redis)
    manager.monitor(db_type=args.db, redis_url=args.redis)

if __name__ == "__main__":
    main()
