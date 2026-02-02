# brain/core/tools/body.py

import aiohttp
import asyncio
import os
import nest_asyncio
from brain.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult
from brain.core.exceptions import ToolExecutionError

BODY_URL = os.getenv("BODY_URL", "http://localhost:9000")

class BodyAdapter(IPPOC_Tool):
    """
    Wraps the Body Subsystem (Rust Node) for side-effects.
    """
    def __init__(self):
        super().__init__(name="body", domain="body")

    def estimate_cost(self, envelope: ToolInvocationEnvelope) -> float:
        # Physical actions are cheaper than cognitive ones? Or expensive?
        # Let's say execution is medium cost.
        return 0.2

    def execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop:
            nest_asyncio.apply()
            return loop.run_until_complete(self._async_execute(envelope))

        return asyncio.run(self._async_execute(envelope))

    async def _async_execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        action = envelope.action
        
        if action == "execute_command":
            return await self._remote_exec(envelope)
        elif action == "economy_balance":
            return await self._get_balance()
        elif action == "network_request":
             # TODO: specific impl
             pass
        
        # Fallback generic execution
        return await self._remote_exec(envelope)

    async def _remote_exec(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        cmd = envelope.context.get("command") or envelope.action
        params = envelope.context.get("params", {})
        
        payload = {
            "action": cmd,
            "params": params,
            "source": envelope.context.get("source", "tool_orchestrator")
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{BODY_URL}/v1/execute", json=payload) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        return ToolResult(
                            success=True,
                            output=text,
                            cost_spent=0.2
                        )
                    else:
                        return ToolResult(
                            success=False,
                            output=f"Body returned {resp.status}",
                            warnings=["Body rejection"]
                        )
            except Exception as e:
                raise ToolExecutionError(envelope.tool_name, f"Body Connection Failed: {e}")

    async def _get_balance(self) -> ToolResult:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{BODY_URL}/v1/economy/balance") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return ToolResult(
                            success=True,
                            output=data,
                            cost_spent=0.1
                        )
                    return ToolResult(
                        success=False,
                        output=f"Balance check failed: {resp.status}",
                        warnings=[f"HTTP {resp.status}"]
                    )
            except Exception as e:
                raise ToolExecutionError("body", f"Body Connection Failed: {e}")
