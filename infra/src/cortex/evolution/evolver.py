# brain/evolution/evolver.py
# @cognitive - IPPOC Evolution Manager

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from cortex.core.ledger import get_ledger
from cortex.core.orchestrator import get_orchestrator
from cortex.core.intents import Intent
from cortex.core.tools.base import ToolInvocationEnvelope
from cortex.evolution.git_driver import GitDriver


class EvolutionStage(str, Enum):
    PROPOSED = "proposed"
    SANDBOXING = "sandboxing"
    TESTING = "testing"
    VALIDATING = "validating"
    MERGING = "merging"
    COMPLETED = "completed"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


@dataclass
class MutationCandidate:
    mutation_id: str
    intent: Intent
    goal: str
    patch_content: str | None = None
    stage: EvolutionStage = EvolutionStage.PROPOSED
    test_results: Dict[str, Any] = field(default_factory=dict)
    rejection_reason: str | None = None
    created_at: float = field(default_factory=time.time)


class Evolver:
    """
    Manages the lifecycle of structural changes (Evolution).
    Enforces the 'Sandbox -> Test -> Merge' loop.
    """
    def __init__(self, repo_path: str = ".") -> None:
        self.orchestrator = get_orchestrator()
        self.ledger = get_ledger()
        self.git = GitDriver(repo_path=repo_path)
        # In a real impl, this State would be persisted to DB/File
        self.active_mutations: Dict[str, MutationCandidate] = {}

    async def propose_mutation(self, intent: Intent, goal: str) -> MutationCandidate:
        """
        Step 1: Accept an intent to evolve.
        """
        mutation = MutationCandidate(
            mutation_id=str(uuid.uuid4()),
            intent=intent,
            goal=goal,
            stage=EvolutionStage.PROPOSED
        )
        
        # 1. Create Git Branch
        res = self.git.create_mutation_branch(mutation.mutation_id)
        if not res["success"]:
             print(f"[Evolver] Failed to create branch: {res.get('error') or res.get('stderr')}")
             mutation.stage = EvolutionStage.REJECTED
             mutation.rejection_reason = "Branch creation failed"
             # Don't add to active if failed? Or keep as failed record?
             # Keep record.
        else:
             print(f"[Evolver] Created mutation branch: {res.get('branch')}")
        
        self.active_mutations[mutation.mutation_id] = mutation
        return mutation

    async def generate_patch(self, mutation_id: str) -> bool:
        """
        Step 2: Use LLM/Coding tools to generate code.
        (Mocked logic for this skeletal implementation)
        """
        mutation = self.active_mutations.get(mutation_id)
        if not mutation:
            return False
            
        # In reality, this would invoke the 'coding_agent' via Orchestrator
        # For now, we simulate generation
        mutation.patch_content = f"# Patch for {mutation.goal}\n# Generated at {time.time()}"
        mutation.stage = EvolutionStage.SANDBOXING
        return True

    async def sandbox_test(self, mutation_id: str) -> bool:
        """
        Step 3: Commit changes and run tests.
        """
        mutation = self.active_mutations.get(mutation_id)
        if not mutation:
            return False

        # 1. Commit the changes made during SANDBOXING
        # We assume the coding agent has modified files by now.
        commit_res = self.git.commit_mutation(f"feat(evolution): {mutation.goal}")
        if not commit_res["success"]:
             # If nothing to commit (clean working tree), that might be okay or an error
             if "nothing to commit" not in str(commit_res.get("stdout", "")):
                 print(f"[Evolver] Commit failed: {commit_res}")
                 mutation.stage = EvolutionStage.REJECTED
                 return False

        mutation.stage = EvolutionStage.TESTING
        
        # 2. Run Tests (Simulated for V1, but can run pytest via subprocess)
        # Mock Logic: Fail if goal contains "dangerous"
        if "dangerous" in mutation.goal.lower():
            mutation.test_results = {"success": False, "error": "Safety violation"}
            # Revert
            self.git.checkout_main()
            return False
            
        # Real Test Execution (Placeholder for V2)
        # test_res = self.git._run(["pytest"])
        
        mutation.test_results = {"success": True, "coverage": 0.85}
        mutation.stage = EvolutionStage.VALIDATING
        return True

    async def validate_and_merge(self, mutation_id: str) -> bool:
        """
        Step 4: Check results, Economy, and Merge.
        """
        mutation = self.active_mutations.get(mutation_id)
        if not mutation:
            return False

        if mutation.stage != EvolutionStage.VALIDATING:
            return False
            
        if not mutation.test_results.get("success"):
            mutation.stage = EvolutionStage.REJECTED
            mutation.rejection_reason = "Tests failed"
            return False

        # Economic Check
        
        mutation.stage = EvolutionStage.MERGING
        
        # 1. Merge
        branch_name = f"ippoc/mutation/{mutation_id}"
        merge_res = self.git.merge_mutation(branch_name)
        
        if not merge_res["success"]:
             print(f"[Evolver] Merge failed: {merge_res}")
             mutation.stage = EvolutionStage.REJECTED
             mutation.rejection_reason = "Merge conflict"
             self.git.checkout_main() # Safety fallback
             return False
        
        print(f"[Evolver] Successfully merged mutation {mutation_id}")
        mutation.stage = EvolutionStage.COMPLETED
        return True

    async def get_status(self, mutation_id: str) -> Optional[MutationCandidate]:
        return self.active_mutations.get(mutation_id)


_evolver_instance: Evolver | None = None

def get_evolver() -> Evolver:
    global _evolver_instance
    if _evolver_instance is None:
        _evolver_instance = Evolver()
    return _evolver_instance
