# brain/tests/verify_autonomy_wiring.py
import asyncio
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from brain.core.autonomy import AutonomyController
from brain.core.ledger import get_ledger

async def main():
    print("--- Verifying Autonomy <-> Observer Wiring ---")
    
    # 1. Initialize Ledger & Seed Pain
    ledger = get_ledger()
    if hasattr(ledger, "init"):
        await ledger.init()

    print("Seeding PAIN (Failures)...")
    for _ in range(5):
        await ledger.create({
            "status": "failed", 
            "tool_name": "fragile_tool", 
            "domain": "test", 
            "action": "break", 
            "duration_ms": 50,
            "cost_spent": 1.0, # Expensive failure
            "error_code": "OUCH"
        })
        
    # 2. Run Autonomy Cycle
    print("Running Autonomy Cycle...")
    controller = AutonomyController()
    
    # Inject a mock orchestrator to avoid actual tool calls during test? 
    # For now, let's just see if it generates the intent.
    # We trap the act() call if possible, or just observe the internal state.
    
    # Run one cycle
    try:
        result = await controller.run_cycle()
        print(f"Cycle Result: {result}")
        
        # 3. Verify Intent Stack
        top_intent = controller.intent_stack.top()
        if top_intent:
            print(f"\n[Generated Intent]")
            print(f"Description: {top_intent.description}")
            print(f"Priority: {top_intent.priority}")
            print(f"Type: {top_intent.intent_type}")
            
            if "pain" in top_intent.description.lower() and top_intent.intent_type == "maintain":
                print("\nSUCCESS: Pain triggered Maintenance Intent.")
            else:
                print("\nFAILURE: Intent generated but did not match expected 'Pain' criteria.")
        else:
            print("\nFAILURE: No intent generated despite high pain.")
            
    except Exception as e:
        print(f"\nERROR during cycle: {e}")
        # Even if execution failed, check if the intent was formed
        top_intent = controller.intent_stack.top()
        if top_intent:
            print(f"\n[Generated Intent (recovered from error)]")
            print(f"Description: {top_intent.description}")
            print(f"Priority: {top_intent.priority}")
            
            if "pain" in top_intent.description.lower() and top_intent.intent_type == "maintain":
                print("\nSUCCESS: Pain triggered Maintenance Intent (Action attempted).")
            else:
                print("\nFAILURE: Intent mismatch.")
        else:
            print("FAILURE: No intent found.")

if __name__ == "__main__":
    asyncio.run(main())
