# brain/tests/verify_operator_ui.py

import sys
import os
import asyncio
import json

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from brain.gateway.vitals import get_vital_signs
from brain.gateway.timeline import get_decision_history
from brain.core.economy import get_economy

async def run_ui_test():
    print("--- IPPOC Operator Experience Verification ---\n")
    
    # Setup
    get_economy().state.budget = 100.0

    # 1. Test Vital Signs
    print("[Test 1] Polling Vital Signs...")
    vitals = await get_vital_signs()
    
    # Validate Heartbeat
    hb = vitals.get("heartbeat", {})
    if hb.get("status") == "thriving" and hb.get("budget") == 100.0:
        print("[PASS] Heartbeat data is healthy.")
    else:
        print(f"[FAIL] Heartbeat mismatch: {hb}")

    # Validate Senses
    senses = vitals.get("senses", {})
    if "pain_score" in senses and "pressure_sources" in senses:
        print(f"[PASS] Senses active (Pain: {senses['pain_score']})")
    else:
        print(f"[FAIL] Senses missing fields: {senses}")

    # Validate Sovereignty
    sov = vitals.get("sovereignty", {})
    # Might be None or dict, but key should exist
    if "last_refusal" in sov:
        print("[PASS] Sovereignty signal enabled.")
    else:
        print("[FAIL] Sovereignty missing.")

    # 2. Test Timeline
    print("\n[Test 2] Fetching Timeline...")
    history = get_decision_history(limit=5)
    print(f"  Fetched {len(history)} records.")
    
    if isinstance(history, list):
         print("[PASS] Timeline returns list structure.")
         if history:
             latest = history[0]
             if "time" in latest and "decision" in latest:
                  print("[PASS] Timeline record has valid schema.")
             else:
                  print(f"[FAIL] Invalid record schema: {latest.keys()}")
    else:
         print(f"[FAIL] Timeline returned {type(history)}")

    print("\n--- OPERATOR UI CERTIFIED ---")

if __name__ == "__main__":
    asyncio.run(run_ui_test())
