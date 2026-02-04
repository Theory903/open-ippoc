from __future__ import annotations

import json
import os
from typing import Dict, Any
from brain.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult
from brain.core.exceptions import ToolExecutionError


class SocialAdapter(IPPOC_Tool):
    """
    Minimal social cognition layer: reputation + mentor queries.
    """
    def __init__(self):
        super().__init__(name="social", domain="social")
        self.path = os.getenv("SOCIAL_MEMORY_PATH", "data/social_memory.json")

    def estimate_cost(self, envelope: ToolInvocationEnvelope) -> float:
        return 0.2

    def execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        action = envelope.action
        if action == "mentor_query":
            return self._mentor_query(envelope)
        if action == "record_interaction":
            return self._record_interaction(envelope)
        if action == "get_reputation":
            return self._get_reputation(envelope)
        raise ToolExecutionError(envelope.tool_name, f"Unknown action: {action}")

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"reputation": {}, "signals": []}

    def _save(self, data: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _mentor_query(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        data = self._load()
        topic = envelope.context.get("topic", "unknown")
        signals = envelope.context.get("signals", {})
        # Basic heuristic: advise to reduce complexity if errors rising
        errors = signals.get("errors_last_hour", 0) or 0
        advice = "Maintain current course."
        if errors > 3:
            advice = "Reduce complexity and increase testing on recent changes."
        return ToolResult(
            success=True,
            output={
                "topic": topic,
                "advice": advice,
                "confidence": 0.7,
                "risk": "medium" if errors > 3 else "low"
            },
            cost_spent=0.2
        )

    def _record_interaction(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        data = self._load()
        actor = envelope.context.get("actor", "unknown")
        delta = float(envelope.context.get("delta", 0.0))
        rep = data["reputation"].get(actor, 0.0)
        data["reputation"][actor] = rep + delta
        data["signals"].append({"actor": actor, "delta": delta, "reason": envelope.context.get("reason", "")})
        self._save(data)
        return ToolResult(success=True, output={"actor": actor, "reputation": data["reputation"][actor]}, cost_spent=0.1)

    def _get_reputation(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        data = self._load()
        actor = envelope.context.get("actor", "unknown")
        return ToolResult(success=True, output={"actor": actor, "reputation": data["reputation"].get(actor, 0.0)}, cost_spent=0.1)
