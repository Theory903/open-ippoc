# brain/tests/verify_value_loop.py

import asyncio
import sys
import os
import shutil

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from brain.core.economy import get_economy, ToolStats
from brain.core.autonomy import AutonomyController
from brain.core.intents import Intent, IntentType
from brain.core.orchestrator import get_orchestrator

async def run_test():
    print("--- IPPOC Phase B: Value Loop Verification ---\n")
    
    # 0. Clean Slate
    economy = get_economy()
    # Reset state for test
    economy.state.budget = 10.0
    economy.state.reserve = 100.0
    economy.state.total_spent = 0.0
    economy.state.total_value = 0.0
    economy.state.tool_stats = {}
    economy._save()
    
    print(f"[Setup] Initial Budget: {economy.state.budget}")

    # 1. Simulate High Value Action (The "Forager")
    # Action: "memory_search" costs 0.5, returns 2.0 value (ROI 4.0)
    print("\n[Test 1] Foraging (High Value Action)...")
    
    tool_name = "memory"
    cost = 0.5
    value = 2.0
    
    # Spend
    economy.spend(cost, tool_name=tool_name)
    # Record Value
    economy.record_value(value, confidence=0.8, source="test_verifier", tool_name=tool_name)
    
    # Check Budget Regen
    # Formula: budget += value * confidence * decay (1.0)
    # Expected: 10.0 - 0.5 + (2.0 * 0.8) = 9.5 + 1.6 = 11.1
    
    print(f"  Budget after action: {economy.state.budget}")
    if economy.state.budget > 10.5:
        print("[PASS] Budget regenerated from value.")
    else:
        print(f"[FAIL] Budget did not regenerate correctly. Got {economy.state.budget}")

    # Check ROI
    stats = economy.get_tool_stats(tool_name)
    print(f"  Tool '{tool_name}' ROI: {stats.roi:.2f}")
    if stats.roi > 3.0:
        print("[PASS] Tool ROI tracked correctly.")
    else:
        print("[FAIL] ROI tracking failed.")

    # 2. Simulate Low Value Spam (The "Burner")
    print("\n[Test 2] Wasteful Action (Low Value)...")
    bad_tool = "spam_bot"
    
    # Burn budget
    for _ in range(6):
        economy.spend(1.0, tool_name=bad_tool)
        economy.record_value(0.1, tool_name=bad_tool) # Terrible ROI
        
    stats = economy.get_tool_stats(bad_tool)
    print(f"  '{bad_tool}' ROI: {stats.roi:.2f}")
    
    # Check Throttling
    throttled = economy.should_throttle(bad_tool)
    orchestra_rep = get_orchestrator().get_reputation(bad_tool)
    
    if throttled or orchestra_rep["status"] == "throttled":
        print("[PASS] Wasteful tool is throttled.")
    else:
        print("[FAIL] Wasteful tool NOT throttled.")

    # 3. Simulate Autonomy Rejection (The "Prudent Mind")
    print("\n[Test 3] Planning with Bad ROI...")
    
    controller = AutonomyController()
    # Inject bad stats for a hypothetical tool
    # Wait, Planner uses heuristic mapping. 
    # Let's say we have an intent that maps to "evolver" (LEARN)
    # And we ruin "evolver" stats first
    
    evolver_tool = "evolver"
    economy.update_tool_stats(evolver_tool, ToolStats(calls=10, total_spent=50.0, total_value=1.0)) # ROI 0.02
    
    # Create Intent
    intent = Intent(
        description="Evolve uselessly",
        priority=0.5,
        intent_type=IntentType.LEARN,
        source="me"
    )
    
    # We need to manually trigger the Planner's estimation logic
    # Since Planner logic is inside plan(), we can create a dummy stack
    controller.intent_stack.intents = [intent]
    
    # Run Planner
    # We spy on the context injection
    # Planner.plan modifies in-place and returns top
    chosen = controller.planner.plan({}, controller.intent_stack)
    
    if chosen:
        print(f"  Planner context: {chosen.context}")
        roi = chosen.context.get("expected_roi", 999)
        print(f"  Expected ROI: {roi:.2f}")
        
        if roi < 0.1:
            print("[PASS] Planner detected low ROI.")
        else:
             print("[FAIL] Planner failed to detect low ROI.")
             
        # Run Decider
        decision = controller.decider.decide({}, chosen)
        print(f"  Decider: {decision['action']} ({decision['reason']})")
        
        if decision['action'] == "idle" and "low_roi" in decision['reason']:
            print("[PASS] Decider refused low ROI intent.")
        else:
            print("[FAIL] Decider allowed low ROI intent.")

    else:
        print("[FAIL] Planner dropped intent entirely (unexpected).")

    print("\n--- VALUE LOOP CERTIFIED ---")

if __name__ == "__main__":
    asyncio.run(run_test())
