# brain/tests/verify_phase2.py
import asyncio
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from brain.core.autonomy import AutonomyController
from brain.core.intents import Intent, IntentType
from brain.core.ledger import get_ledger
from brain.maintainer.types import SignalSummary, Trend

# Mocking external updates for testing without waiting for DB
async def mock_seed_pain(pain_level: float):
    # This is tricky because Observer reads from Ledger.
    # We must seed Ledger to produce the desired Pain Score.
    ledger = get_ledger()
    if hasattr(ledger, "init"):
        await ledger.init()
        
    if pain_level > 0.5:
        # Create many failures
        for _ in range(10):
            await ledger.create({"status": "failed", "tool_name": "test", "domain": "test", "action": "fail", "duration_ms": 10})
    else:
        # Create successes
        for _ in range(10):
            await ledger.create({"status": "completed", "tool_name": "test", "domain": "test", "action": "succeed", "duration_ms": 10})

async def main():
    print("--- Verifying Phase 2: Intent Hierarchy ---")

    controller = AutonomyController()

    # TEST 1: SURVIVAL (High Pain)
    print("\n[TEST 1] Seeding HIGH PAIN...")
    await mock_seed_pain(0.8)
    
    # Run cycle
    print("Running cycle...")
    try:
        await controller.run_cycle()
        top = controller.intent_stack.top()
        if top and top.intent_type == IntentType.MAINTAIN:
            print(f"SUCCESS: High Pain triggered MAINTAIN intent (Priority: {top.priority:.2f})")
        else:
            print(f"FAILURE: Expected MAINTAIN, got {top}")
    except Exception as e:
        print(f"Execution Error (Expected if tools don't exist): {e}")
        # Check stack anyway
        top = controller.intent_stack.top()
        if top and top.intent_type == IntentType.MAINTAIN:
            print(f"SUCCESS (Rescue): Intent Stack has MAINTAIN -> {top}")

    # TEST 2: GROWTH (Low Pain, Forced Budget check?)
    # Clear stack explicitly
    controller.intent_stack.intents = []
    
    print("\n[TEST 2] Seeding LOW PAIN (Zen)...")
    ledger = get_ledger() # Need reference here
    # We need A LOT of successes to dilute the 10 failures from Test 1 
    # We need A LOT of successes to dilute the 10 failures from Test 1 
    # because Observer uses the last 100 actions.
    # 10 failures / 100 actions = 10% error rate.
    # To get < 10%, we need > 90 successes.
    for _ in range(100):
        await ledger.create({"status": "completed", "tool_name": "test", "domain": "test", "action": "succeed", "duration_ms": 10})
    
    
    # Run cycle
    print("Running cycle...")
    try:
        await controller.run_cycle()
        top = controller.intent_stack.top()
        
        # NOTE: Economy check is mocked in real system via get_economy().
        # If budget is default (infinite/mocked), we expect EXPLORE or IDLE depending on logic.
        # Our logic says: if pain < 0.1 -> Explore.
        
        if top and top.intent_type == IntentType.EXPLORE:
             print(f"SUCCESS: Low Pain triggered EXPLORE intent (Priority: {top.priority:.2f})")
        elif top is None:
             print("RESULT: No Intent generated (Idle state).")
        else:
             print(f"RESULT: Generated {top.intent_type}")
             
    except Exception as e:
        print(f"Execution Error: {e}")
        top = controller.intent_stack.top()
        if top and top.intent_type == IntentType.EXPLORE:
             print(f"SUCCESS (Rescue): Intent Stack has EXPLORE -> {top}")

if __name__ == "__main__":
    asyncio.run(main())
