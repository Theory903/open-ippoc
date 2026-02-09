from __future__ import annotations

from ippoc.cortex.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult, CognitiveRole
from ippoc.cortex.core.exceptions import ToolExecutionError
from ippoc.cortex.maintainer.scheduler import maintainer_tick


class MaintainerAdapter(IPPOC_Tool):
    """
    Wraps the infrastructure maintenance and restoration subsystem.
    """
    def __init__(self):
        super().__init__(name="maintainer", domain="body", role=CognitiveRole.SURVIVOR)

    def estimate_cost(self, envelope: ToolInvocationEnvelope) -> float:
        return 1.0

    def execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        if envelope.action not in ["tick", "maintain"]:
            raise ToolExecutionError(envelope.tool_name, f"Unknown action: {envelope.action}")
        maintainer_tick()
        return ToolResult(success=True, output={"status": "maintainer_tick_complete"}, cost_spent=1.0)
