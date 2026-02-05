import sys
from unittest.mock import MagicMock

# Mock dependencies before import to avoid ImportErrors for missing packages
sys.modules["cortex.cortex.two_tower"] = MagicMock()
sys.modules["cortex.cortex.telepathy"] = MagicMock()
sys.modules["langgraph.graph"] = MagicMock()
sys.modules["langchain_core"] = MagicMock()
sys.modules["langchain_google_genai"] = MagicMock()

import pytest
from unittest.mock import patch
from cortex.cortex.langgraph_engine import LangGraphEngine
from cortex.core.tools.base import ToolInvocationEnvelope

@pytest.fixture
def mock_dependencies():
    with patch("cortex.cortex.langgraph_engine.get_orchestrator") as mock_get_orch, \
         patch("cortex.cortex.langgraph_engine.TwoTowerEngine") as mock_tt, \
         patch("cortex.cortex.langgraph_engine.TelepathySwarm") as mock_swarm:

        mock_orch = MagicMock()
        mock_get_orch.return_value = mock_orch

        # Mock invoke to return a dummy result
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.output = "OK"
        mock_orch.invoke.return_value = mock_result

        yield {
            "orchestrator": mock_orch,
            "two_tower": mock_tt,
            "swarm": mock_swarm
        }

@pytest.mark.asyncio
async def test_risk_assessment_execute_command(mock_dependencies):
    engine = LangGraphEngine(mock_dependencies["two_tower"], mock_dependencies["swarm"])

    state = {
        "proposed_action": MagicMock(action="execute_command", payload={"cmd": "rm -rf /"})
    }

    await engine.execute(state)

    # Check invoke call
    mock_orch = mock_dependencies["orchestrator"]
    assert mock_orch.invoke.called
    envelope = mock_orch.invoke.call_args[0][0]
    assert isinstance(envelope, ToolInvocationEnvelope)
    assert envelope.action == "execute_command"
    assert envelope.risk_level == "high"

@pytest.mark.asyncio
async def test_risk_assessment_network_request(mock_dependencies):
    engine = LangGraphEngine(mock_dependencies["two_tower"], mock_dependencies["swarm"])

    state = {
        "proposed_action": MagicMock(action="network_request", payload={"url": "http://evil.com"})
    }

    await engine.execute(state)

    envelope = mock_dependencies["orchestrator"].invoke.call_args[0][0]
    assert envelope.risk_level == "high"

@pytest.mark.asyncio
async def test_risk_assessment_file_operation(mock_dependencies):
    engine = LangGraphEngine(mock_dependencies["two_tower"], mock_dependencies["swarm"])

    state = {
        "proposed_action": MagicMock(action="file_operation", payload={"path": "/etc/passwd"})
    }

    await engine.execute(state)

    envelope = mock_dependencies["orchestrator"].invoke.call_args[0][0]
    assert envelope.risk_level == "high"

@pytest.mark.asyncio
async def test_risk_assessment_economy_balance(mock_dependencies):
    engine = LangGraphEngine(mock_dependencies["two_tower"], mock_dependencies["swarm"])

    state = {
        "proposed_action": MagicMock(action="economy_balance", payload={})
    }

    await engine.execute(state)

    envelope = mock_dependencies["orchestrator"].invoke.call_args[0][0]
    assert envelope.risk_level == "low"

@pytest.mark.asyncio
async def test_risk_assessment_openclaw_skill(mock_dependencies):
    engine = LangGraphEngine(mock_dependencies["two_tower"], mock_dependencies["swarm"])

    state = {
        "proposed_action": MagicMock(action="openclaw_scan", payload={})
    }

    await engine.execute(state)

    envelope = mock_dependencies["orchestrator"].invoke.call_args[0][0]
    assert envelope.risk_level == "medium"

@pytest.mark.asyncio
async def test_risk_assessment_default_medium(mock_dependencies):
    engine = LangGraphEngine(mock_dependencies["two_tower"], mock_dependencies["swarm"])

    state = {
        "proposed_action": MagicMock(action="unknown_action", payload={})
    }

    await engine.execute(state)

    envelope = mock_dependencies["orchestrator"].invoke.call_args[0][0]
    assert envelope.risk_level == "medium"
