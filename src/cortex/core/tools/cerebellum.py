# brain/core/tools/cerebellum.py

from typing import Dict, Any, Optional
from cortex.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult
import asyncio
import os
import nest_asyncio # Imported here for consistency, though it's in execute method in snippet
import importlib.util
from pathlib import Path

class CerebellumAdapter(IPPOC_Tool):
    """
    Adapter for the Cerebellum (Research & Learning Engine).
    Wraps: brain/cerebellum/
    """
    def __init__(self):
        super().__init__(name="research", domain="cognition")
        self.binary_path = os.path.abspath("brain/cerebellum/target/release/cerebellum")
        self.use_binary = os.path.exists(self.binary_path)
        if self.use_binary:
            print(f"[Cerebellum] Rust Kernel Detected at {self.binary_path}. High Performance Mode: ON")
        else:
            print(f"[Cerebellum] Rust Kernel not found. Falling back to Python Simulation.")

    def estimate_cost(self, envelope: ToolInvocationEnvelope) -> float:
        # Research is expensive (reading papers, processing tokens)
        if envelope.action == "digest_paper":
            return 2.0
        return 0.5

    def execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        """
        Standard execution entry point.
        """
        action = envelope.action
        kwargs = envelope.context

        # If binary exists, use it for compute intensive tasks
        if self.use_binary and action == "digest_paper":
            binary_res = self._execute_binary(kwargs)
            return ToolResult(
                success="error" not in binary_res,
                output=binary_res,
                cost_spent=2.0
            )
        
        # Else confirm loop and run mock
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

    def _execute_binary(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        import subprocess
        import json
        
        query = ctx.get("query", "research request")
        
        try:
            # cerebellum think "query"
            result = subprocess.run(
                [self.binary_path, "think", query],
                capture_output=True, text=True, check=True
            )
            data = json.loads(result.stdout)
            return {"status": "digested (rust)", "output": data}
        except Exception as e:
            return {"error": f"Rust Kernel Panic: {e}", "details": str(e)}

    async def _async_execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Mock Logic (Fallback)
        """
        if action == "digest_paper":
            url = kwargs.get("url")
            return {
                "summary": f"Digested {url} (Python Simulation)",
                "key_findings": ["Pattern A", "Pattern B"],
                "relevance_score": 0.85
            }
        elif action == "learn_skill":
            skill_name = kwargs.get("skill_name")
            return {
                "status": "learned",
                "skill": skill_name,
                "proficiency": 0.1
            }
        elif action in ["think", "reason", "analyze"]:
            prompt = kwargs.get("prompt") or kwargs.get("query") or ""
            context = kwargs.get("context") or []
            engine = self._load_phi4()
            if engine:
                return engine.reason(prompt, context)
            return {
                "thought": "Reasoning engine unavailable. Returning fallback response.",
                "conclusion": prompt[:200],
                "confidence": 0.5
            }
        else:
            # Assuming ToolExecutionError is defined elsewhere or needs to be added
            # For now, returning a generic error dict
            return {"error": f"Unknown action: {action}"}

    def _load_phi4(self) -> Optional[Any]:
        """
        Load the Phi-4 reasoning engine via file path (directory name contains a hyphen).
        """
        phi_path = Path(__file__).resolve().parents[2] / "cortex" / "reasoning-engine" / "phi4.py"
        if not phi_path.exists():
            return None
        try:
            spec = importlib.util.spec_from_file_location("ippoc_phi4", str(phi_path))
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.Phi4Reasoning()
        except Exception:
            return None

    # The original _digest_paper and _learn_skill methods are replaced by the new _async_execute logic.
    # Keeping the original _digest_paper method signature as it was part of the original document
    # but its implementation is now effectively handled by the new _async_execute for fallback.
    # This method will likely become unused or needs to be refactored to align with the new API.
    async def _digest_paper(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        url = envelope.context.get("url")
        if not url:
            return ToolResult(success=False, output="Missing 'url' in context")
            
        # Mocking the actual PDF read/parse logic
        # In future, this calls the Rust cerebellum crate or Python logic
        summary = f"Digested paper from {url}. Key findings: [Mock Data]"
        
        return ToolResult(
            success=True,
            output={"summary": summary, "vectors_created": 15},
            cost_spent=2.0,
            memory_written=True # Learning implies memory write
        )

    async def _learn_skill(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        topic = envelope.context.get("topic")
        # Mock logic
        return ToolResult(
            success=True,
            output=f"Skill '{topic}' acquired. Added to graph.",
            cost_spent=0.5,
            memory_written=True
        )
