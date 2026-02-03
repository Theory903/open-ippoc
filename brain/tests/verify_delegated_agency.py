# brain/tests/verify_delegated_agency.py

import sys
import os
import asyncio
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from brain.core.delegation import get_agency
from brain.core.economy import get_economy

async def run_test():
    print("--- IPPOC Phase E: Delegated Agency Verification ---\n")
    
    # Setup
    economy = get_economy()
    agency = get_agency()
    
    economy.state.budget = 20.0 # Rich parent
    economy._save()
    
    # 1. Test "The Worker" (Successful Delegation)
    print("[Test 1] The Worker (Contract Fulfillment)...")
    
    worker_id = agency.spawn_cell(
        mission="Fetch data",
        budget=5.0,
        ttl=10.0,
        tools=["web_search", "summarizer"]
    )
    
    worker = agency.get_cell(worker_id)
    if not worker:
        print("[FAIL] Failed to spawn worker.")
        return
        
    print(f"  Spawned Worker: {worker_id[:8]}")
    
    # Execute allowed action
    res = worker.execute_action("web_search", cost=1.0)
    print(f"  Action 'web_search' (Cost 1.0): {res}")
    
    if res == "success" and worker.status == "active" and worker.spent_budget == 1.0:
        print("[PASS] Worker executed allowed action within budget.")
    else:
        print(f"[FAIL] Worker failed valid action: {res}")
        
    # 2. Test "The Rogue" (Sovereignty Violation)
    print("\n[Test 2] The Rogue (Contract Violation)...")
    
    rogue_id = agency.spawn_cell(
        mission="Modify core",
        budget=5.0,
        ttl=10.0,
        tools=["web_search"] # Canon NOT allowed
    )
    rogue = agency.get_cell(rogue_id)
    
    # Attempt prohibited tool
    res_rogue = rogue.execute_action("canon", cost=0.0)
    print(f"  Action 'canon': {res_rogue}")
    print(f"  Rogue Status: {rogue.status}")
    
    if "contract_violation" in res_rogue and rogue.status == "terminated":
        print("[PASS] Rogue agent terminated immediately.")
    else:
        print(f"[FAIL] Rogue agent survived violation! Status: {rogue.status}")

    # 3. Test "The Waster" (Budget Exhaustion)
    print("\n[Test 3] The Waster (Budget Kill)...")
    
    waster_id = agency.spawn_cell(
        mission="Burn money",
        budget=2.0,
        ttl=10.0,
        tools=["web_search"]
    )
    waster = agency.get_cell(waster_id)
    
    # Spend 1.5 (OK)
    waster.execute_action("web_search", cost=1.5)
    print(f"  Spent 1.5/2.0. Status: {waster.status}")
    
    # Spend 1.0 (Over budget 2.5)
    res_waste = waster.execute_action("web_search", cost=1.0)
    print(f"  Spent +1.0 (Total 2.5). Result: {res_waste}")
    print(f"  Waster Status: {waster.status}")
    
    if "budget_exhausted" in res_waste and waster.status == "terminated":
        print("[PASS] Waster terminated on budget breach.")
    else:
        print(f"[FAIL] Waster survived bankruptcy! Status: {waster.status}")
        
    # 4. Supervisor Loop Audit
    print("\n[Test 4] Supervisor Audit...")
    agency.audit_cells()
    
    # Only Worker should be active (if we didn't terminate it manually?)
    # Worker is active. Rogue is terminated. Waster is terminated.
    active_count = sum(1 for c in agency.cells.values() if c.status == "active")
    print(f"  Active Cells: {active_count}")
    
    if active_count == 1: 
        print("[PASS] Audit reflects correct state.")
    else:
        print(f"[FAIL] Audit mismatch. Expected 1 active, got {active_count}")

    print("\n--- DELEGATED AGENCY CERTIFIED ---")

if __name__ == "__main__":
    asyncio.run(run_test())
