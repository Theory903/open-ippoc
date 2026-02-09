import unittest
from ippoc.cortex.core.orchestrator import ToolOrchestrator
from ippoc.cortex.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult, CognitiveRole
from ippoc.cortex.core.exceptions import SecurityViolation

class MockTool(IPPOC_Tool):
    def estimate_cost(self, envelope): return 0.0
    def execute(self, envelope): return ToolResult(success=True)

class TestHostileAudit(unittest.TestCase):
    def setUp(self):
        self.orchestrator = ToolOrchestrator()
        # Reset tools for clean test
        self.orchestrator.tools = {}

    def test_actor_delete_allowed(self):
        """
        Verify that ACTOR tools ARE allowed to perform 'delete' actions.
        (Previously blocked by precedence bug).
        """
        actor_tool = MockTool(name="actor_tool", domain="body", role=CognitiveRole.ACTOR)
        self.orchestrator.register(actor_tool)
        
        envelope = ToolInvocationEnvelope(
            tool_name="actor_tool",
            domain="body",
            action="delete_temp_file",
            risk_level="low"
        )
        
        # This SHOULD succeed now
        result = self.orchestrator.invoke(envelope)
        self.assertTrue(result.success)

    def test_sensor_blocked_overwrite(self):
        """
        Verify that SENSOR tools are blocked from 'overwrite' actions.
        (Broadened side-effect check).
        """
        sensor_tool = MockTool(name="sensor_tool", domain="memory", role=CognitiveRole.SENSOR)
        self.orchestrator.register(sensor_tool)
        
        envelope = ToolInvocationEnvelope(
            tool_name="sensor_tool",
            domain="memory",
            action="overwrite_record",
            risk_level="low"
        )
        
        with self.assertRaises(SecurityViolation):
            self.orchestrator.invoke(envelope)
        
        # NOTE: We do NOT assert on async violation emission here.
        # Capability enforcement (SecurityViolation) is synchronous and blocking.
        # Telemetry emission is best-effort and async, so it won't happen 
        # in this sync test harness without an event loop. Ideally correct.

    def test_planner_delete_allowed(self):
        """
        Verify that PLANNER tools ARE allowed to perform 'delete' actions.
        """
        planner_tool = MockTool(name="planner_tool", domain="cognition", role=CognitiveRole.PLANNER)
        self.orchestrator.register(planner_tool)
        
        envelope = ToolInvocationEnvelope(
            tool_name="planner_tool",
            domain="cognition",
            action="delete_thought",
            risk_level="low"
        )
        
        result = self.orchestrator.invoke(envelope)
        self.assertTrue(result.success)

if __name__ == "__main__":
    unittest.main()
