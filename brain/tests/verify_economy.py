# brain/tests/verify_economy.py
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from brain.core.economy import get_economy

def main():
    print("--- Verifying Phase 3: Economy ---")
    
    # 1. Reset Economy
    # Force a temporary path for testing to avoid messing up real state
    test_path = "data/test_economy.json"
    if os.path.exists(test_path):
        os.remove(test_path)
    
    os.environ["ECONOMY_PATH"] = test_path
    # Re-initialize
    economy = get_economy()
    economy.path = test_path
    economy.state = economy._load()
    
    # TEST 1: Throttling (High Failure Rate)
    print("\n[TEST 1] Testing Failure Throttling...")
    tool_bad = "buggy_tool"
    
    # Fail 15 times
    for _ in range(15):
        economy.spend(0.1, tool_bad, failed=True)
     
    throttled = economy.check_throttle(tool_bad)
    stats = economy.get_tool_stats(tool_bad)
    
    if throttled and stats.error_rate == 1.0:
        print(f"SUCCESS: Tool '{tool_bad}' throttled. Error Rate: {stats.error_rate:.2f}")
    else:
        print(f"FAILURE: Tool NOT throttled. Throttled: {throttled}, Error Rate: {stats.error_rate}")

    # TEST 2: Throttling (Bad ROI)
    print("\n[TEST 2] Testing ROI Throttling...")
    tool_expensive = "money_pit"
    
    # Spend a lot ($10), get zero value
    economy.spend(10.0, tool_expensive, failed=False)
    economy.record_value(0.0, tool_expensive)
    
    throttled = economy.check_throttle(tool_expensive)
    stats = economy.get_tool_stats(tool_expensive)
    
    if throttled and stats.roi == 0.0:
        print(f"SUCCESS: Tool '{tool_expensive}' throttled by ROI. Spent: {stats.total_spent}, Value: {stats.total_value}")
    else:
        print(f"FAILURE: Tool NOT throttled. Throttled: {throttled}, ROI: {stats.roi}")

    # TEST 3: Budget Priority
    print("\n[TEST 3] Testing Priority Budgeting...")
    # Drain budget to 10.0 (Reserve is default 100.0)
    economy.state.budget = 15.0 
    economy.state.reserve = 100.0
    
    # Reserve threshold for Low Priority = 30% of 100 = 30.0
    # Current budget 15.0 < 30.0 -> Should FAIL for Low Priority
    
    can_explore = economy.check_budget(priority=0.2)
    can_maintain = economy.check_budget(priority=0.9)
    
    if not can_explore:
        print("SUCCESS: Low priority blocked (Budget 15 < Reserve 30)")
    else:
        print("FAILURE: Low priority allowed!")
        
    if can_maintain:
        print("SUCCESS: High priority allowed (Budget 15 > 0)")
    else:
        print("FAILURE: High priority blocked!")

if __name__ == "__main__":
    main()
