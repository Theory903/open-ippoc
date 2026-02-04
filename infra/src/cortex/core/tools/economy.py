from __future__ import annotations

from cortex.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult
from cortex.core.economy import get_economy
from cortex.core.exceptions import ToolExecutionError
from cortex.core.orchestrator import require_spine


class EconomyAdapter(IPPOC_Tool):
    """
    Exposes economy state for inspection and controlled updates.
    """
    def __init__(self):
        super().__init__(name="economy", domain="economy")
        self.economy = get_economy()

    def estimate_cost(self, envelope: ToolInvocationEnvelope) -> float:
        return 0.05

    def execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        require_spine()
        action = envelope.action
        if action == "snapshot":
            return ToolResult(success=True, output=self.economy.snapshot(), cost_spent=0.05)
        if action == "record_value":
            value = float(envelope.context.get("value", 0.0))
            tool = envelope.context.get("tool")
            self.economy.record_value(value, tool_name=tool)
            return ToolResult(success=True, output={"value": value, "roi": self.economy.roi()}, cost_spent=0.05)
        if action == "tick":
            self.economy.tick()
            return ToolResult(success=True, output=self.economy.snapshot(), cost_spent=0.05)
        raise ToolExecutionError(envelope.tool_name, f"Unknown action: {action}")
