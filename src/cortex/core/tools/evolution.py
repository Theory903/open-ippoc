# brain/core/tools/evolution.py

import os
import asyncio
from typing import Optional
from cortex.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult
from cortex.core.exceptions import ToolExecutionError, SecurityViolation
# Assuming cortex.evolution has a propose_mutation function
# from cortex.evolution import propose_mutation

class EvolutionAdapter(IPPOC_Tool):
    """
    Wraps the Evolution Engine (Git/Self-Modification).
    """
    def __init__(self):
        super().__init__(name="evolution", domain="evolution")

    def estimate_cost(self, envelope: ToolInvocationEnvelope) -> float:
        # Evolution is high-stakes and potentially high-compute if simulation is needed
        return 5.0 # Expensive

    def execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        # In a real system, this would likely be async.
        return asyncio.run(self._async_execute(envelope))

    async def _async_execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        if envelope.action == "propose_patch":
            return await self._propose_patch(envelope)
        else:
            raise ToolExecutionError(envelope.tool_name, f"Unknown action: {envelope.action}")

    async def _propose_patch(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        # Mandatory Context Validation
        env_type = envelope.context.get("environment")
        if env_type not in ["sandbox", "stable"]:
            raise ToolExecutionError(envelope.tool_name, "Context missing valid 'environment' (sandbox|stable)")

        if env_type == "stable" and not envelope.requires_validation:
            raise SecurityViolation("Stable evolution requires validation flag")
        if envelope.sandboxed and env_type == "stable":
            raise SecurityViolation("Sandboxed executions cannot mutate stable environment")
            
        diff_code = envelope.context.get("diff")
        if not diff_code:
             raise ToolExecutionError(envelope.tool_name, "Context missing 'diff'")
             
        # Mocking the actual call to cortex.evolution for now
        # In full implementation: proposal_id = cortex.evolution.propose(diff_code)
        proposal_id = f"prop_{os.urandom(4).hex()}"
        
        return ToolResult(
            success=True,
            output={"proposal_id": proposal_id, "status": "queued_for_sandbox" if env_type == "stable" else "applied_sandbox"},
            # Evolution writes to disk/git, so it's a "memory write" effectively
            memory_written=True,
            rollback_token=proposal_id, 
            cost_spent=5.0
        )
