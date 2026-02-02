# brain/tests/verify_memory.py
import asyncio
import os
import sys
import time

# Ensure project root is in path
sys.path.append(os.getcwd())

from brain.memory.consolidation import get_hippocampus

async def main():
    print("--- Verifying Phase 5: Memory Consolidation ---")
    
    hippocampus = get_hippocampus()
    
    # 1. Add Memories
    print("Adding memories...")
    # Important memory
    mem1 = await hippocampus.add_memory("Important Fact", importance=1.0)
    # Trivial memory
    mem2 = await hippocampus.add_memory("Noise", importance=0.05)
    
    print(f"Memory Count: {len(hippocampus.memories)}")
    
    # 2. Simulate Time Passage (Decay)
    # We can't wait 24 hours, so Hack time or Decay function?
    # We'll just manually tweak the last_accessed time to be OLD.
    
    # Make mem1 old but it started high (1.0)
    # 24 hours ago
    hippocampus.memories[mem1.memory_id].last_accessed -= 86400.0 
    
    # Make mem2 old and it started low (0.05)
    hippocampus.memories[mem2.memory_id].last_accessed -= 86400.0
    
    # 3. Consolidate (Sleep)
    print("Running Consolidation (Sleep)...")
    stats = await hippocampus.consolidate()
    print(f"Stats: {stats}")
    
    # 4. Verify Survival
    remaining = hippocampus.memories
    if mem1.memory_id in remaining:
        # 1.0 * 0.5^1 = 0.5 -> Should survive (> 0.1)
        print("SUCCESS: Important memory survived decay.")
        current_imp = remaining[mem1.memory_id].importance
        print(f"  New Importance: {current_imp:.4f} (Expected ~0.5)")
    else:
        print("FAILURE: Important memory was wrongly pruned.")

    if mem2.memory_id not in remaining:
        # 0.05 * 0.5^1 = 0.025 -> Should be pruned (< 0.1)
        print("SUCCESS: Trivial memory was pruned.")
    else:
        print("FAILURE: Trivial memory NOT pruned.")
        print(f"  Importance: {remaining[mem2.memory_id].importance}")

if __name__ == "__main__":
    asyncio.run(main())
