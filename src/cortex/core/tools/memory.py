import requests
import logging
import os
import json
from brain.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult
from brain.core.exceptions import ToolExecutionError

# Configure Logging
logger = logging.getLogger("IPPOC.Memory")

# Configuration
MEMORY_URL = os.getenv("MEMORY_URL", "http://127.0.0.1:8000")
HIDB_URL = os.getenv("HIDB_URL", os.getenv("BODY_URL", "http://127.0.0.1:9000"))
MEMORY_BACKEND = os.getenv("MEMORY_BACKEND", "api")  # api|hidb|auto
MEMORY_TIMEOUT_S = int(os.getenv("MEMORY_TIMEOUT_S", "30")) # 30 seconds
MEMORY_MAX_RETRIES = int(os.getenv("MEMORY_MAX_RETRIES", "1"))
IDENTITY_PATH = os.getenv("IDENTITY_MEMORY_PATH", "data/identity_memory.json")
SKILL_PATH = os.getenv("SKILL_MEMORY_PATH", "data/skill_memory.json")

class MemoryAdapter(IPPOC_Tool):
    """
    Wraps the Memory Subsystem (HiDB/Rust) as a tool.
    """
    def __init__(self):
        super().__init__(name="memory", domain="memory")

    def estimate_cost(self, envelope: ToolInvocationEnvelope) -> float:
        # Memory is now free
        return 0.0

    def execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        action = envelope.action
        
        try:
            if action == "store_episodic":
                return self._store_memory(envelope)
            elif action == "retrieve":
                return self._retrieve_memory(envelope)
            elif action == "store_identity":
                return self._store_identity(envelope)
            elif action == "get_identity":
                return self._get_identity()
            elif action == "store_skill":
                return self._store_skill(envelope)
            elif action == "get_skills":
                return self._get_skills()
            else:
                 raise ToolExecutionError(envelope.tool_name, f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Memory Tool Error ({action}): {e}")
            return ToolResult(success=False, output=f"Memory Error: {str(e)}", warnings=[str(e)])

    def _store_memory(self, envelope: ToolInvocationEnvelope) -> ToolResult:
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
            return self._post_with_retries(
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
            return self._post_with_retries(
                f"{HIDB_URL}/v1/memory/store",
                payload_hidb,
                envelope,
                success_message="stored"
            )

        return ToolResult(success=False, output=f"Unknown memory backend: {MEMORY_BACKEND}")

    def _retrieve_memory(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        query = envelope.context.get("query")
        if not query:
             raise ToolExecutionError(envelope.tool_name, "Missing 'query' in context")

        limit = envelope.context.get("limit", 5)
        payload = {"query": query, "limit": limit}

        backend = MEMORY_BACKEND.lower()
        if backend == "auto":
            backend = "api"

        if backend == "api":
            return self._post_with_retries(
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
            return self._post_with_retries(
                f"{HIDB_URL}/v1/memory/search",
                payload_hidb,
                envelope,
                success_message="search"
            )

        return ToolResult(success=False, output=f"Unknown memory backend: {MEMORY_BACKEND}")

    def _post_with_retries(self, url: str, payload: dict, envelope: ToolInvocationEnvelope, success_message: str) -> ToolResult:
        timeout_s = (envelope.deadline_ms / 1000) if envelope.deadline_ms else (envelope.context.get("timeout_ms", 30000) / 1000)
        max_retries = envelope.context.get("max_retries", MEMORY_MAX_RETRIES)
        attempt = 0

        while attempt <= max_retries:
            try:
                resp = requests.post(url, json=payload, timeout=timeout_s)
                if resp.status_code == 200:
                    data = resp.json()
                    return ToolResult(
                        success=True,
                        output=data,
                        memory_written=True if success_message == "consolidated" else False,
                        cost_spent=self.estimate_cost(envelope)
                    )
                if resp.status_code in (500, 502, 503):
                    attempt += 1
                    if attempt > max_retries:
                        return ToolResult(success=False, output=f"{success_message} failed: {resp.status_code}", warnings=[f"HTTP {resp.status_code}"])
                    import time
                    time.sleep(0.5)
                    continue
                return ToolResult(success=False, output=f"{success_message} failed: {resp.status_code}", warnings=[f"HTTP {resp.status_code}"])
            except Exception as e:
                attempt += 1
                error_detail = f"{type(e).__name__}: {str(e)}"
                logger.error(f"Memory Connection Error to {url}: {error_detail}")
                if attempt > max_retries:
                    return ToolResult(success=False, output=f"Connection Failed: {error_detail}", warnings=[error_detail])
                import time
                time.sleep(0.5)
        return ToolResult(success=False, output=f"{success_message} failed after retries")

    def _load_json(self, path: str, default: dict) -> dict:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return default
        return default

    def _save_json(self, path: str, data: dict) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _store_identity(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        identity = envelope.context.get("identity")
        if not isinstance(identity, dict):
            raise ToolExecutionError(envelope.tool_name, "Missing identity dict")
        data = self._load_json(IDENTITY_PATH, {})
        data.update(identity)
        self._save_json(IDENTITY_PATH, data)
        return ToolResult(success=True, output={"identity": data}, memory_written=True, cost_spent=0.0)

    def _get_identity(self) -> ToolResult:
        data = self._load_json(IDENTITY_PATH, {})
        return ToolResult(success=True, output={"identity": data}, cost_spent=0.0)

    def _store_skill(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        skill = envelope.context.get("skill")
        success = bool(envelope.context.get("success", True))
        if not skill:
            raise ToolExecutionError(envelope.tool_name, "Missing skill name")
        data = self._load_json(SKILL_PATH, {})
        entry = data.get(skill, {"success": 0, "fail": 0})
        if success:
            entry["success"] += 1
        else:
            entry["fail"] += 1
        data[skill] = entry
        self._save_json(SKILL_PATH, data)
        return ToolResult(success=True, output={"skill": skill, "stats": entry}, memory_written=True, cost_spent=0.0)

    def _get_skills(self) -> ToolResult:
        data = self._load_json(SKILL_PATH, {})
        return ToolResult(success=True, output={"skills": data}, cost_spent=0.0)
