# brain/tests/verify_evolution.py

import os
import shutil
import tempfile
import asyncio
import subprocess
import sys
import uuid

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from brain.evolution.evolver import Evolver, EvolutionStage
from brain.core.intents import Intent, IntentType

class EvolutionTestEnvironment:
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="ippoc_evo_test_")
        self.repo_path = self.test_dir
        
    def setup_git(self):
        print(f"[Test] Setting up temp git repo at {self.repo_path}")
        subprocess.run(["git", "init"], cwd=self.repo_path, check=True, capture_output=True)
        # Configure user for commit
        subprocess.run(["git", "config", "user.email", "ippoc@test.com"], cwd=self.repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "IPPOC Test"], cwd=self.repo_path, check=True)
        
        # Initial commit
        with open(os.path.join(self.repo_path, "dna.txt"), "w") as f:
            f.write("Original DNA")
        subprocess.run(["git", "add", "dna.txt"], cwd=self.repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial DNA"], cwd=self.repo_path, check=True)
        
        # Rename master to main if needed
        subprocess.run(["git", "branch", "-M", "main"], cwd=self.repo_path, check=True)

    def cleanup(self):
        print(f"[Test] Cleaning up {self.test_dir}")
        shutil.rmtree(self.test_dir)

async def run_test():
    env = EvolutionTestEnvironment()
    try:
        env.setup_git()
        
        # Initialize Evolver with the temp repo
        # Note: We need to use 'main' as base, GitDriver defaults to checking out from current.
        evolver = Evolver(repo_path=env.repo_path)
        
        print("--- Step 1: Propose Mutation ---")
        intent = Intent(description="Evolve DNA", intent_type=IntentType.LEARN, source="test", priority=0.8)
        mutation = await evolver.propose_mutation(intent, goal="Upgrade DNA to V2")
        
        if mutation.stage == EvolutionStage.REJECTED:
            print("[FAIL] Mutation rejected at proposal")
            return
            
        print(f"[PASS] Mutation proposed on branch: ippoc/mutation/{mutation.mutation_id}")
        
        # Verify branch exists
        res = subprocess.run(
            ["git", "branch", "--list", f"ippoc/mutation/{mutation.mutation_id}"], 
            cwd=env.repo_path, capture_output=True, text=True
        )
        if mutation.mutation_id not in res.stdout:
            print("[FAIL] Branch not found in git")
            return
            
        print("--- Step 2: Modify Code (Simulated) ---")
        # Simulate the coding agent modifying a file
        with open(os.path.join(env.repo_path, "dna.txt"), "w") as f:
            f.write("Evolved DNA V2")
            
        print("--- Step 3: Sandbox Test ---")
        success = await evolver.sandbox_test(mutation.mutation_id)
        if not success:
            print("[FAIL] Sandbox test failed")
            return
            
        if mutation.stage != EvolutionStage.VALIDATING:
            print(f"[FAIL] Stage mismatch. Expected VALIDATING, got {mutation.stage}")
            return
            
        print("[PASS] Sandbox test passed. Changes committed.")
        
        print("--- Step 4: Validate and Merge ---")
        success = await evolver.validate_and_merge(mutation.mutation_id)
        if not success:
            print("[FAIL] Merge failed")
            return
            
        if mutation.stage != EvolutionStage.COMPLETED:
             print(f"[FAIL] Stage mismatch. Expected COMPLETED, got {mutation.stage}")
             return

        # Verify Merge content
        with open(os.path.join(env.repo_path, "dna.txt"), "r") as f:
            content = f.read()
            
        if content == "Evolved DNA V2":
            print("[PASS] Evolution Complete: DNA successfully mutated and merged.")
            print("*** EVOLUTION CERTIFIED ***")
        else:
            print(f"[FAIL] DNA mismatch. Got: {content}")

        print("\n--- Step 5: Toxic Mutation (Revert Test) ---")
        toxic_intent = Intent(description="Destroy DNA", intent_type=IntentType.LEARN, source="test", priority=0.8)
        toxic_mutation = await evolver.propose_mutation(toxic_intent, goal="Make dangerous changes")
        
        # Simulate toxic change
        with open(os.path.join(env.repo_path, "dna.txt"), "w") as f:
            f.write("TOXIC DNA")
            
        success = await evolver.sandbox_test(toxic_mutation.mutation_id)
        if success:
            print("[FAIL] Toxic mutation should have failed sandbox test")
            return
            
        print("[PASS] Toxic mutation correctly failed sandbox test.")
        
        # Verify content on main is still safe (Evolver should checkout main or revert)
        # sandbox_test logic for failure: self.git.checkout_main()
        with open(os.path.join(env.repo_path, "dna.txt"), "r") as f:
            content = f.read()
            
        if content == "Evolved DNA V2":
            print("[PASS] System correctly reverted/checked-out main. DNA is safe.")
        else:
            print(f"[FAIL] Safety system failed. DNA is corrupted: {content}")

    except Exception as e:
        print(f"[ERROR] Test crashed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        env.cleanup()

if __name__ == "__main__":
    asyncio.run(run_test())
