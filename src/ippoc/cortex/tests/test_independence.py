# brain/tests/test_independence.py
import os
import json
import time
import asyncio
from fastapi.testclient import TestClient
from ippoc.cortex.cortex.server import app, IPPOC_API_KEY, system_state
from ippoc.cortex.core.orchestrator import get_orchestrator

# Auth Header
HEADERS = {"Authorization": f"Bearer {IPPOC_API_KEY}"}

def run_independence_tests():
    print("🚀 Starting Independence Verification...")
    
    # 1. Structural Independence: Boot without OpenClaw
    # The TestClient triggers the lifespan event
    with TestClient(app) as client:
        print("✅ IPPOC-OS Booted successfully.")
        
        # 2. Verify native registration
        orc = get_orchestrator()
        assert "native_shell" in orc.tools, "Native shell tool missing!"
        print("✅ Native Shell Registered.")
        
        # 3. Autonomy Independence: Check autonomy control
        # Force autonomy on for test
        resp = client.post("/v1/system/autonomy/control", params={"action": "on"}, headers=HEADERS)
        assert resp.status_code == 200
        assert system_state.autonomy_enabled is True
        print("✅ Autonomy Control (ON) verified.")
        
        # 4. Cognitive Independence: Intent creation via CLI (API)
        resp = client.post("/v1/intents/create", json={"goal": "Test standalone reflection", "urgency": 0.9}, headers=HEADERS)
        assert resp.status_code == 200
        print("✅ Manual Intent Creation verified.")
        
        # 5. Native Ingest: Ingest sensory signal
        resp = client.post("/v1/signals/ingest", json={
            "type": "SIGHT",
            "content": "Simulated independent observation",
            "source": "ci_test",
            "confidence": 1.0
        }, headers=HEADERS)
        assert resp.status_code == 200
        print("✅ Standalone Signal Ingestion verified.")

        # 6. Verify Sensors are running
        # We wait a bit or just check system_state
        assert system_state.sensor_task is not None
        print("✅ Internal Sensors active.")

        # 7. Diagnostics verify independence
        resp = client.get("/health", headers=HEADERS)
        data = resp.json()
        assert "native_shell" in data.get("tools_loaded", [])
        print("✅ Diagnostics confirmed independence tools.")

        # 8. Shutdown test
        resp = client.post("/v1/system/autonomy/control", params={"action": "off"}, headers=HEADERS)
        assert resp.status_code == 200
        assert system_state.autonomy_enabled is False
        print("✅ Autonomy Control (OFF) verified.")

    print("\n🏆 IPPOC INDEPENDENCE VERIFIED: 100%")

if __name__ == "__main__":
    # Ensure environment is set for test
    os.environ["IPPOC_AUTONOMY"] = "true"
    os.environ["IPPOC_HEARTBEAT_SECONDS"] = "1"
    os.environ["IPPOC_SENSOR_INTERVAL"] = "1"
    
    try:
        run_independence_tests()
    except Exception as e:
        print(f"❌ Independence Test Failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
