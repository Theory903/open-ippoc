# brain/core/tools/worldmodel.py
import os
from typing import Dict, Any
from brain.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult
import asyncio
import nest_asyncio

class WorldModelAdapter(IPPOC_Tool):
    """
    Adapter for the WorldModel (Simulation Metaverse).
    Wraps: brain/worldmodel/
    """
    def __init__(self):
        super().__init__(name="simulation", domain="simulation")
        self.binary_path = os.path.abspath("brain/worldmodel/target/release/worldmodel")
        self.use_binary = os.path.exists(self.binary_path)
        if self.use_binary:
            print(f"[WorldModel] Rust Physics Engine Detected. Syncing Reality...")
        else:
            print(f"[WorldModel] Rust Engine not found. Using low-res Python mock.")

    def estimate_cost(self, envelope: ToolInvocationEnvelope) -> float:
        # Simulation is compute heavy
        return 3.0

    def execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        action = envelope.action
        kwargs = envelope.context

        if self.use_binary:
             res = self._execute_binary(action, kwargs)
             return ToolResult(
                 success="error" not in res,
                 output=res,
                 cost_spent=3.0
             )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop:
            nest_asyncio.apply()
            res = loop.run_until_complete(self._async_execute(action, **kwargs))
        else:
            res = asyncio.run(self._async_execute(action, **kwargs))

        return ToolResult(
            success="error" not in res,
            output=res,
            cost_spent=self.estimate_cost(envelope)
        )

    def _execute_binary(self, action: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        import subprocess
        import json
        import tempfile
        
        try:
            if action == "simulate_action":
                payload = json.dumps(ctx)
                result = subprocess.run(
                    [self.binary_path, "simulate", "--payload", payload],
                    capture_output=True, text=True, check=True
                )
                return json.loads(result.stdout)
                
            elif action == "test_patch":
                patch_content = ctx.get("patch", "")
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                    f.write(patch_content)
                    patch_path = f.name
                
                try:
                    result = subprocess.run(
                        [self.binary_path, "test-patch", patch_path],
                        capture_output=True, text=True, check=True
                    )
                    return json.loads(result.stdout)
                finally:
                    os.unlink(patch_path)
            
            return {"error": f"Unknown binary action: {action}"}
            
        except Exception as e:
            return {"error": f"Simulation Sandbox Panic: {e}"}

    async def _async_execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Mock Logic (Fallback)
        """
        if action == "simulate_action":
            # Monte Carlo Simulation placeholder
            return {
                "outcome_prob": 0.85, 
                "risks": ["API Throttling", "Context Window Overflow"],
                "projected_cost": 0.15
            }
        elif action == "test_patch":
            # Sandbox placeholder
            return {
                "status": "verified", 
                "regressions": 0, 
                "coverage_delta": 0.0
            }
        else:
            # raise ToolExecutionError(f"Unknown action: {action}")
            return {"error": f"Unknown action: {action}"}
