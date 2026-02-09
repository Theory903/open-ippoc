# brain/tests/test_policy_integration.py

import os
import pytest
from unittest.mock import MagicMock, patch
from cortex.core.orchestrator import ToolOrchestrator, ToolInvocationEnvelope, IPPOC_Tool, ToolResult
from cortex.core.exceptions import SecurityViolation

# Mock Tool
class MockTool(IPPOC_Tool):
    def __init__(self, name="mock.tool", domain="memory"):
        super().__init__(name, domain)
    def estimate_cost(self, envelope):
        return 0.1
    def execute(self, envelope):
        return ToolResult(success=True, output="ok")

@pytest.fixture
def orchestrator():
    # Reset singleton if possible, or just instantiate new one
    ToolOrchestrator._instance = None
    with patch.dict(os.environ, {"ORCHESTRATOR_AUDIT_PATH": "/dev/null"}): # Mock audit path
        orch = ToolOrchestrator()

        # Mock economy to prevent file writes
        orch.economy = MagicMock()
        orch.economy.should_throttle.return_value = False
        orch.economy.snapshot.return_value = {"budget": 100}

        orch.register(MockTool())

        # Also mock _audit_action to be safe
        orch._audit_action = MagicMock()

        return orch

def test_orchestrator_policy_deny(orchestrator):
    # Set up a policy that denies everything
    from cortex.core.policy import PolicyRule, PolicyEffect
    orchestrator.policy_engine.rules.append(
        PolicyRule("deny_all", PolicyEffect.DENY, {})
    )

    envelope = ToolInvocationEnvelope(tool_name="mock.tool", domain="memory", action="read")

    with pytest.raises(SecurityViolation, match="Policy 'deny_all' denied action"):
        orchestrator.invoke(envelope)

def test_orchestrator_policy_allow(orchestrator):
    # Default behavior is allow if no rules match
    orchestrator.policy_engine.rules = [] # Clear rules

    envelope = ToolInvocationEnvelope(tool_name="mock.tool", domain="memory", action="read")
    result = orchestrator.invoke(envelope)
    assert result.success is True

def test_orchestrator_env_integration():
    # This test is tricky because ToolOrchestrator reads env vars at INIT.
    # We need to patch env BEFORE init.
    ToolOrchestrator._instance = None
    with patch.dict(os.environ, {
        "ORCHESTRATOR_TOOL_DENYLIST": "mock.tool",
        "ORCHESTRATOR_AUDIT_PATH": "/dev/null"
    }):
        orch = ToolOrchestrator()
        # Mock dependencies
        orch.economy = MagicMock()
        orch.economy.should_throttle.return_value = False
        orch.economy.snapshot.return_value = {"budget": 100}
        orch._audit_action = MagicMock()

        orch.register(MockTool())

        envelope = ToolInvocationEnvelope(tool_name="mock.tool", domain="memory", action="read")
        with pytest.raises(SecurityViolation, match="Policy 'env_tool_denylist' denied action"):
            orch.invoke(envelope)
