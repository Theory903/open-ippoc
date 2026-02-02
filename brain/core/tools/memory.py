# brain/core/tools/memory.py

import aiohttp
import asyncio
import os
import nest_asyncio
from brain.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult
from brain.core.exceptions import ToolExecutionError

# Configuration
MEMORY_URL = os.getenv("MEMORY_URL", "http://localhost:8000")
HIDB_URL = os.getenv("HIDB_URL", os.getenv("BODY_URL", "http://localhost:9000"))
MEMORY_BACKEND = os.getenv("MEMORY_BACKEND", "api")  # api|hidb|auto
MEMORY_TIMEOUT_MS = int(os.getenv("MEMORY_TIMEOUT_MS", "8000"))
MEMORY_MAX_RETRIES = int(os.getenv("MEMORY_MAX_RETRIES", "1"))

class MemoryAdapter(IPPOC_Tool):
    """
    Wraps the Memory Subsystem (HiDB/Rust) as a tool.
    """
    def __init__(self):
        super().__init__(name="memory", domain="memory")

    def estimate_cost(self, envelope: ToolInvocationEnvelope) -> float:
        # Writes are expensive, reads are cheap
        if "store" in envelope.action:
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

        backend = MEMORY_BACKEND.lower()
        if backend == "auto":
            backend = "api"

        if backend == "api":
            return await self._post_with_retries(
                f"{MEMORY_URL}/v1/memory/consolidate",
                payload,
                envelope,
                success_message="consolidated"
            )

        if backend == "hidb":
            vector = envelope.context.get("vector")
            if not vector:
                return ToolResult(success=False, output="Missing vector for HiDB store", warnings=["hidb requires vector"])
            payload_hidb = {"content": content, "vector": vector}
            return await self._post_with_retries(
                f"{HIDB_URL}/v1/memory/store",
                payload_hidb,
                envelope,
                success_message="stored"
            )

        return ToolResult(success=False, output=f"Unknown memory backend: {MEMORY_BACKEND}")

    async def _retrieve_memory(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        query = envelope.context.get("query")
        if not query:
             raise ToolExecutionError(envelope.tool_name, "Missing 'query' in context")

        limit = envelope.context.get("limit", 5)
        payload = {"query": query, "limit": limit}

        backend = MEMORY_BACKEND.lower()
        if backend == "auto":
            backend = "api"

        if backend == "api":
            return await self._post_with_retries(
                f"{MEMORY_URL}/v1/memory/search",
                payload,
                envelope,
                success_message="search"
            )

        if backend == "hidb":
            vector = envelope.context.get("vector")
            if not vector:
                return ToolResult(success=False, output="Missing vector for HiDB search", warnings=["hidb requires vector"])
            payload_hidb = {"vector": vector, "limit": limit}
            return await self._post_with_retries(
                f"{HIDB_URL}/v1/memory/search",
                payload_hidb,
                envelope,
                success_message="search"
            )

        return ToolResult(success=False, output=f"Unknown memory backend: {MEMORY_BACKEND}")

    async def _post_with_retries(self, url: str, payload: dict, envelope: ToolInvocationEnvelope, success_message: str) -> ToolResult:
        timeout_ms = envelope.deadline_ms or envelope.context.get("timeout_ms") or MEMORY_TIMEOUT_MS
        max_retries = envelope.context.get("max_retries", MEMORY_MAX_RETRIES)
        attempt = 0

        while attempt <= max_retries:
            try:
                timeout = aiohttp.ClientTimeout(total=timeout_ms / 1000)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, json=payload) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return ToolResult(
                                success=True,
                                output=data,
                                memory_written=True if success_message == "consolidated" else False,
                                cost_spent=self.estimate_cost(envelope)
                            )
                        if resp.status in (500, 502, 503):
                            attempt += 1
                            if attempt > max_retries:
                                return ToolResult(success=False, output=f"{success_message} failed: {resp.status}", warnings=[f"HTTP {resp.status}"])
                            continue
                        return ToolResult(success=False, output=f"{success_message} failed: {resp.status}", warnings=[f"HTTP {resp.status}"])
            except Exception as e:
                attempt += 1
                if attempt > max_retries:
                    raise ToolExecutionError(envelope.tool_name, f"Connection Failed: {e}")
        return ToolResult(success=False, output=f"{success_message} failed after retries")
