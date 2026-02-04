from __future__ import annotations

from brain.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult
from brain.core.exceptions import ToolExecutionError
from brain.maintainer.scheduler import maintainer_tick


class MaintainerAdapter(IPPOC_Tool):
    """
    Wraps the internal maintainer loop so it can be invoked via orchestrator.
    """
    def __init__(self):
        super().__init__(name="maintainer", domain="cognition")

    def estimate_cost(self, envelope: ToolInvocationEnvelope) -> float:
        return 1.0

    def execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        if envelope.action not in ["tick", "maintain"]:
            raise ToolExecutionError(envelope.tool_name, f"Unknown action: {envelope.action}")
        maintainer_tick()
        return ToolResult(success=True, output={"status": "maintainer_tick_complete"}, cost_spent=1.0)
