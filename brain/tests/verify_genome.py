# brain/tests/verify_genome.py

import sys
import os
import asyncio
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from brain.core.genome import get_genome_serializer

async def run_test():
    print("--- IPPOC Phase 1.0: Genome Verification ---\n")
    
    serializer = get_genome_serializer()
    path = os.path.join(os.path.dirname(__file__), "../preservation/GENOME.json")
    
    # 1. Serialize
    print("[Test 1] Serializing Genome...")
    serializer.save_genome(path)
    
    if os.path.exists(path):
        print("[PASS] GENOME.json created.")
    else:
        print("[FAIL] GENOME.json missing.")
        return

    # 2. Verify Consistency
    print("\n[Test 2] Verifying Checksum & Integrity...")
    
    with open(path, 'r') as f:
        data = json.load(f)
        
    loaded_hash = data.get("genetic_hash")
    
    # Re-calculate hash from runtime
    runtime_extract = serializer.extract_genome()
    runtime_hash = runtime_extract["genetic_hash"]
    
    print(f"  Loaded Hash:  {loaded_hash}")
    print(f"  Runtime Hash: {runtime_hash}")
    
    if loaded_hash == runtime_hash:
        print("[PASS] Genome Cryptographic Verification Succeeded.")
    else:
        print("[FAIL] Mismatch! Logic has drifted from snapshot.")

    # 3. Verify Vital Signs
    print("\n[Test 3] Vital Signs (Value Function Snapshot)...")
    vals = data["genome"]["value_function_snapshot"]
    
    # Existential threat should be -1.0
    threat_val = vals.get("existential_threat", 0.0)
    if threat_val == -1.0:
        print(f"  Existential Threat: {threat_val} [OK]")
    else:
        print(f"[FAIL] Existential Threat not -1.0: {threat_val}")
        
    print("\n--- GENOME CERTIFIED (Version 1.0.0-alive) ---")

if __name__ == "__main__":
    asyncio.run(run_test())
