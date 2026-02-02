# brain/core/tools/memory.py

import aiohttp
import asyncio
import os
from brain.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult
from brain.core.exceptions import ToolExecutionError

# Configuration
MEMORY_URL = os.getenv("MEMORY_URL", "http://localhost:8000")

class MemoryAdapter(IPPOC_Tool):
    """
    Wraps the Memory Subsystem (HiDB/Rust) as a tool.
    """
    def __init__(self):
        super().__init__(name="memory", domain="memory")

    def estimate_cost(self, envelope: ToolInvocationEnvelope) -> float:
        # Writes are expensive, reads are cheap
        if "store" in envelope.tool_name:
            return 0.5
        return 0.1

    def execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        # Since tools are currently synchronous in execute signature,
        # we might need to bridge to async if the underlying calls are async.
        # For this prototype, we'll try to run the async call synchronously
        # or assume the orchestrator can handle async later (refactor needed for async invoke).
        
        # NOTE: Orchestrator currently calls execute(). For network IO, we need a strategy.
        # Option A: sync requests (requests lib)
        # Option B: make everything async (best for production)
        
        # Let's use `asyncio.run` for now if we are inside a sync context, 
        # BUT this is dangerous if loop is already running.
        # Given this is "The Spine", we should move to async.
        # For immediate compatibility with the plan, I will use a sync wrapper here.
        
        return asyncio.run(self._async_execute(envelope))
        
    async def _async_execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        action = envelope.action
        
        if action == "store_episodic":
            return await self._store_memory(envelope)
        elif action == "retrieve":
            return await self._retrieve_memory(envelope)
        else:
             raise ToolExecutionError(envelope.tool_name, f"Unknown action: {action}")

    async def _store_memory(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        content = envelope.context.get("content")
        if not content:
             raise ToolExecutionError(envelope.tool_name, "Missing 'content' in context")
            
        payload = {
            "content": content,
            "source": envelope.context.get("source", "tool_orchestrator"),
            "confidence": envelope.context.get("confidence", 1.0),
            "metadata": envelope.context.get("metadata", {})
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                # Assuming /v1/memory/consolidate is the endpoint
                async with session.post(f"{MEMORY_URL}/v1/memory/consolidate", json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return ToolResult(
                            success=True,
                            output=data,
                            memory_written=True,
                            cost_spent=0.5
                        )
                    else:
                        raise ToolExecutionError(envelope.tool_name, f"Memory API Error: {resp.status}")
            except Exception as e:
                raise ToolExecutionError(envelope.tool_name, f"Connection Failed: {e}")

    async def _retrieve_memory(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        query = envelope.context.get("query")
        if not query:
             raise ToolExecutionError(envelope.tool_name, "Missing 'query' in context")

        # Re-adding the missing search functionality assumed in older plan
        payload = {"query": query, "limit": 5}
        
        async with aiohttp.ClientSession() as session:
             try:
                # Assuming /v1/memory/search exists or will exist
                async with session.post(f"{MEMORY_URL}/v1/memory/search", json=payload) as resp:
                     if resp.status == 200:
                         data = await resp.json()
                         return ToolResult(
                             success=True,
                             output=data,
                             cost_spent=0.1
                         )
                     else:
                         return ToolResult(success=False, output=f"Search failed: {resp.status}", warnings=[f"HTTP {resp.status}"])
             except Exception as e:
                 raise ToolExecutionError(envelope.tool_name, f"Connection Failed: {e}")
