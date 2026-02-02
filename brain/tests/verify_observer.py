# brain/tests/verify_observer.py
import asyncio
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from brain.maintainer.observer import collect_signals
from brain.core.ledger import get_ledger

async def main():
    print("--- Verifying IPPOC Observer ---")
    
    # 1. Initialize Ledger (if needed)
    ledger = get_ledger()
    if hasattr(ledger, "init"):
        await ledger.init()
        
    # 2. Populate some dummy data to verify logic
    print("Seeding dummy data...")
    # Success
    await ledger.create({
        "status": "completed", 
        "tool_name": "test_tool", 
        "domain": "test", 
        "action": "ping", 
        "duration_ms": 100,
        "cost_spent": 0.01
    })
    # Failure
    await ledger.create({
        "status": "failed", 
        "tool_name": "test_tool", 
        "domain": "test", 
        "action": "explode", 
        "duration_ms": 50,
        "cost_spent": 0.01,
        "error_code": "BOOM"
    })
    
    # 3. Collect Signals
    print("Collecting signals...")
    summary = await collect_signals()
    
    # 4. Report
    print(f"\n[Observation Result]")
    print(f"Pain Score: {summary.pain_score}")
    print(f"Trend: {summary.trend}")
    print(f"Confidence: {summary.confidence}")
    print(f"Pressure Sources: {summary.pressure_sources}")
    print(f"Raw Metrics: {summary.raw_metrics}")
    
    if summary.confidence > 0.0:
        print("\nSUCCESS: Observer is functioning.")
    else:
        print("\nFAILURE: Observer returned zero confidence/empty data.")

if __name__ == "__main__":
    asyncio.run(main())
