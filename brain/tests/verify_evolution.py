# brain/tests/verify_evolution.py
import asyncio
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from brain.core.autonomy import AutonomyController
from brain.core.intents import Intent, IntentType
from brain.evolution.evolver import get_evolver, EvolutionStage

async def main():
    print("--- Verifying Phase 4: Evolution Loop ---")
    
    # 1. Setup
    controller = AutonomyController()
    evolver = get_evolver()
    
    # 2. Force a LEARN intent
    print("Injecting LEARN intent...")
    intent = Intent(
        description="Optimize memory recall speed",
        priority=0.9, # High priority to ensure selection
        intent_type=IntentType.LEARN,
        source="verification_script"
    )
    controller.intent_stack.add(intent)
    
    # 3. Run Cycle -> Should trigger Evolver
    print("Running Autonomy Cycle...")
    result = await controller.run_cycle()
    print(f"Cycle Result: {result}")
    
    # 4. Verify Evolution Triggered
    result_data = result.get("result", {})
    mutation_id = result_data.get("mutation_id")
    
    if not mutation_id:
        print("FAILURE: No mutation_id returned in result.")
        return

    print(f"SUCCESS: Mutation started with ID: {mutation_id}")
    
    # 5. Verify Evolver State
    mutation = await evolver.get_status(mutation_id)
    if not mutation:
        print("FAILURE: Mutation not found in Evolver.")
        return
        
    print(f"Mutation Stage (Initial): {mutation.stage}")
    if mutation.stage in (EvolutionStage.PROPOSED, EvolutionStage.SANDBOXING):
        print("SUCCESS: Mutation in correct initial stage.")
    else:
        print(f"FAILURE: Unexpected stage {mutation.stage}")
    
    # 6. Manually advance lifecycle (Simulate background worker)
    print("Advancing lifecycle (Simulating worker)...")
    await evolver.sandbox_test(mutation_id)
    print(f"Mutation Stage (After Test): {mutation.stage}")
    
    await evolver.validate_and_merge(mutation_id)
    print(f"Mutation Stage (Final): {mutation.stage}")
    
    if mutation.stage == EvolutionStage.COMPLETED:
        print("SUCCESS: Full Evolution Loop completed.")
    else:
        print("FAILURE: Evolution did not complete.")

if __name__ == "__main__":
    asyncio.run(main())
