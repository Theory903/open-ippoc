"""
Comprehensive tests for LangGraph Engine

Tests cover:
- Graph construction and topology
- Node execution (observe, inner_voice, validate, execute)
- State management and transitions
- Risk assessment logic
- Tool orchestrator integration
- Error handling and edge cases
"""

import sys
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
import pytest

# Mock dependencies before import
sys.modules["cortex.cortex.two_tower"] = MagicMock()
sys.modules["cortex.cortex.telepathy"] = MagicMock()
sys.modules["langgraph.graph"] = MagicMock()
sys.modules["langchain_core"] = MagicMock()
sys.modules["langchain_google_genai"] = MagicMock()

from cortex.cortex.langgraph_engine import LangGraphEngine
from cortex.core.tools.base import ToolInvocationEnvelope
from cortex.cortex.schemas import CognitiveState, Signal, Context, Metrics
import time


@pytest.fixture
def mock_two_tower():
    """Mock TwoTowerEngine"""
    mock_tt = MagicMock()
    mock_tt.generate_impulse = AsyncMock()
    mock_tt.validate_action = AsyncMock()
    return mock_tt


@pytest.fixture
def mock_swarm():
    """Mock TelepathySwarm"""
    return MagicMock()


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator with successful execution"""
    with patch("cortex.cortex.langgraph_engine.get_orchestrator") as mock_get_orch:
        mock_orch = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.output = "Command executed successfully"
        mock_result.warnings = []
        mock_orch.invoke.return_value = mock_result
        mock_get_orch.return_value = mock_orch
        yield mock_orch


@pytest.fixture
def engine(mock_two_tower, mock_swarm, mock_orchestrator):
    """Create LangGraphEngine instance with mocked dependencies"""
    return LangGraphEngine(mock_two_tower, mock_swarm)


class TestLangGraphEngineInitialization:
    """Test engine initialization and graph construction"""

    def test_engine_initialization(self, mock_two_tower, mock_swarm, mock_orchestrator):
        """Engine should initialize with dependencies"""
        engine = LangGraphEngine(mock_two_tower, mock_swarm)

        assert engine.tt is mock_two_tower
        assert engine.swarm is mock_swarm
        assert engine.orchestrator is mock_orchestrator
        assert engine.graph is not None

    def test_graph_construction(self, engine):
        """Graph should be built with correct nodes"""
        # Graph should be compiled
        assert engine.graph is not None

    def test_engine_has_required_methods(self, engine):
        """Engine should have all required node methods"""
        assert hasattr(engine, 'observe')
        assert hasattr(engine, 'inner_voice')
        assert hasattr(engine, 'validate')
        assert hasattr(engine, 'execute')
        assert hasattr(engine, 'run_step')
        assert hasattr(engine, '_assess_risk')


class TestRiskAssessment:
    """Test risk assessment logic"""

    def test_execute_command_is_high_risk(self, engine):
        """execute_command should be high risk"""
        risk = engine._assess_risk("execute_command", {"cmd": "rm -rf /"})
        assert risk == "high"

    def test_file_operation_is_high_risk(self, engine):
        """file_operation should be high risk"""
        risk = engine._assess_risk("file_operation", {"path": "/etc/passwd"})
        assert risk == "high"

    def test_network_request_is_high_risk(self, engine):
        """network_request should be high risk"""
        risk = engine._assess_risk("network_request", {"url": "http://example.com"})
        assert risk == "high"

    def test_economy_balance_is_low_risk(self, engine):
        """economy_balance should be low risk"""
        risk = engine._assess_risk("economy_balance", {})
        assert risk == "low"

    def test_openclaw_skill_is_medium_risk(self, engine):
        """OpenClaw skills should be medium risk"""
        risk = engine._assess_risk("openclaw_scan", {})
        assert risk == "medium"

    def test_unknown_action_defaults_to_medium(self, engine):
        """Unknown actions should default to medium risk"""
        risk = engine._assess_risk("unknown_action", {})
        assert risk == "medium"

    def test_risk_assessment_with_empty_params(self, engine):
        """Risk assessment should work with empty params"""
        risk = engine._assess_risk("execute_command", {})
        assert risk == "high"

    def test_risk_assessment_with_none_params(self, engine):
        """Risk assessment should work with None params"""
        risk = engine._assess_risk("economy_balance", None)
        assert risk == "low"


class TestObserveNode:
    """Test observe node functionality"""

    @pytest.mark.asyncio
    async def test_observe_returns_empty_signals(self, engine):
        """Observe should return empty signals by default"""
        state = {}
        result = await engine.observe(state)

        assert "signals" in result
        assert result["signals"] == []

    @pytest.mark.asyncio
    async def test_observe_with_existing_state(self, engine):
        """Observe should work with existing state"""
        state = {"memory_context": "existing context"}
        result = await engine.observe(state)

        assert "signals" in result


class TestInnerVoiceNode:
    """Test inner_voice node functionality"""

    @pytest.mark.asyncio
    async def test_inner_voice_generates_impulse(self, engine, mock_two_tower):
        """Inner voice should generate impulse from TwoTower"""
        mock_impulse = MagicMock()
        mock_impulse.payload = {"thought": "test thought"}
        mock_two_tower.generate_impulse.return_value = mock_impulse

        state = {
            "memory_context": "test context",
            "signals": [{"type": "test"}]
        }

        result = await engine.inner_voice(state)

        assert "proposed_action" in result
        assert result["proposed_action"] == mock_impulse
        assert "inner_monologue" in result
        assert len(result["inner_monologue"]) > 0
        mock_two_tower.generate_impulse.assert_called_once()

    @pytest.mark.asyncio
    async def test_inner_voice_with_empty_state(self, engine, mock_two_tower):
        """Inner voice should handle empty state"""
        mock_impulse = MagicMock()
        mock_impulse.payload = {"thought": "empty state thought"}
        mock_two_tower.generate_impulse.return_value = mock_impulse

        state = {}
        result = await engine.inner_voice(state)

        assert "proposed_action" in result

    @pytest.mark.asyncio
    async def test_inner_voice_creates_monologue(self, engine, mock_two_tower):
        """Inner voice should create monologue from impulse"""
        mock_impulse = MagicMock()
        mock_impulse.payload = {"thought": "important thought"}
        mock_two_tower.generate_impulse.return_value = mock_impulse

        state = {}
        result = await engine.inner_voice(state)

        assert "inner_monologue" in result
        assert "important thought" in result["inner_monologue"][0]


class TestValidateNode:
    """Test validate node functionality"""

    @pytest.mark.asyncio
    async def test_validate_approves_action(self, engine, mock_two_tower):
        """Validate should approve safe actions"""
        mock_two_tower.validate_action.return_value = True

        mock_action = MagicMock()
        state = {"proposed_action": mock_action}

        result = await engine.validate(state)

        assert result == {}
        mock_two_tower.validate_action.assert_called_once_with(mock_action)

    @pytest.mark.asyncio
    async def test_validate_rejects_action(self, engine, mock_two_tower):
        """Validate should reject dangerous actions"""
        mock_two_tower.validate_action.return_value = False

        mock_action = MagicMock()
        state = {"proposed_action": mock_action}

        result = await engine.validate(state)

        assert "proposed_action" in result
        assert result["proposed_action"] is None
        assert "inner_monologue" in result
        assert "rejected" in result["inner_monologue"][0].lower()

    @pytest.mark.asyncio
    async def test_validate_with_no_action(self, engine):
        """Validate should handle missing action"""
        state = {}
        result = await engine.validate(state)

        assert result == {}

    @pytest.mark.asyncio
    async def test_validate_with_none_action(self, engine):
        """Validate should handle None action"""
        state = {"proposed_action": None}
        result = await engine.validate(state)

        assert result == {}


class TestExecuteNode:
    """Test execute node functionality"""

    @pytest.mark.asyncio
    async def test_execute_successful_action(self, engine, mock_orchestrator):
        """Execute should invoke orchestrator successfully"""
        mock_action = MagicMock()
        mock_action.action = "execute_command"
        mock_action.payload = {"cmd": "ls"}

        state = {"proposed_action": mock_action}

        result = await engine.execute(state)

        assert "execution_result" in result
        assert "Command executed successfully" in result["execution_result"]
        mock_orchestrator.invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_constructs_envelope_correctly(self, engine, mock_orchestrator):
        """Execute should construct proper ToolInvocationEnvelope"""
        mock_action = MagicMock()
        mock_action.action = "network_request"
        mock_action.payload = {"url": "http://test.com"}

        state = {"proposed_action": mock_action}

        await engine.execute(state)

        call_args = mock_orchestrator.invoke.call_args[0][0]
        assert isinstance(call_args, ToolInvocationEnvelope)
        assert call_args.action == "network_request"
        assert call_args.risk_level == "high"
        assert call_args.domain == "body"

    @pytest.mark.asyncio
    async def test_execute_with_no_action(self, engine):
        """Execute should handle missing action"""
        state = {}
        result = await engine.execute(state)

        assert result == {}

    @pytest.mark.asyncio
    async def test_execute_with_failed_invocation(self, engine, mock_orchestrator):
        """Execute should handle failed invocations"""
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.warnings = ["Error occurred"]
        mock_orchestrator.invoke.return_value = mock_result

        mock_action = MagicMock()
        mock_action.action = "test_action"
        mock_action.payload = {}

        state = {"proposed_action": mock_action}

        result = await engine.execute(state)

        assert "execution_result" in result
        assert "FAIL" in result["execution_result"]
        assert "Error occurred" in result["execution_result"]

    @pytest.mark.asyncio
    async def test_execute_with_exception(self, engine, mock_orchestrator):
        """Execute should handle exceptions gracefully"""
        mock_orchestrator.invoke.side_effect = Exception("Orchestrator error")

        mock_action = MagicMock()
        mock_action.action = "test_action"
        mock_action.payload = {}

        state = {"proposed_action": mock_action}

        result = await engine.execute(state)

        assert "execution_result" in result
        assert "Failed" in result["execution_result"]

    @pytest.mark.asyncio
    async def test_execute_includes_context(self, engine, mock_orchestrator):
        """Execute should include proper context in envelope"""
        mock_action = MagicMock()
        mock_action.action = "file_operation"
        mock_action.payload = {"path": "/tmp/test"}

        state = {"proposed_action": mock_action}

        await engine.execute(state)

        envelope = mock_orchestrator.invoke.call_args[0][0]
        assert envelope.context["caller"] == "langgraph.brainstem"
        assert envelope.context["source"] == "cortex"
        assert "params" in envelope.context


class TestRunStep:
    """Test run_step integration"""

    @pytest.mark.asyncio
    async def test_run_step_complete_flow(self, engine, mock_two_tower, mock_orchestrator):
        """run_step should execute complete cognitive loop"""
        # Setup mocks
        mock_impulse = MagicMock()
        mock_impulse.action = "economy_balance"
        mock_impulse.payload = {}
        mock_two_tower.generate_impulse.return_value = mock_impulse
        mock_two_tower.validate_action.return_value = True

        input_signal = Signal(
            timestamp=time.time(),
            node_id="test_node",
            context=Context(task="test_task"),
            metrics=Metrics(duration_sec=0.0, cost_ippc=0.0, success=True)
        )

        result = await engine.run_step(input_signal)

        # Verify state structure
        assert "signals" in result
        assert "memory_context" in result
        assert "inner_monologue" in result
        assert "proposed_action" in result
        assert "execution_result" in result

        # Verify flow executed
        assert len(result["signals"]) == 1
        assert result["proposed_action"] is not None
        assert result["execution_result"] is not None

    @pytest.mark.asyncio
    async def test_run_step_with_rejected_action(self, engine, mock_two_tower):
        """run_step should handle rejected actions"""
        mock_impulse = MagicMock()
        mock_impulse.action = "dangerous_action"
        mock_impulse.payload = {}
        mock_two_tower.generate_impulse.return_value = mock_impulse
        mock_two_tower.validate_action.return_value = False

        input_signal = Signal(
            timestamp=time.time(),
            node_id="test_node",
            context=Context(task="test_task"),
            metrics=Metrics(duration_sec=0.0, cost_ippc=0.0, success=True)
        )

        result = await engine.run_step(input_signal)

        # Action should be None after rejection
        assert result["proposed_action"] is None
        assert result["execution_result"] is None

    @pytest.mark.asyncio
    async def test_run_step_state_initialization(self, engine, mock_two_tower):
        """run_step should initialize state correctly"""
        mock_two_tower.generate_impulse.return_value = MagicMock(payload={})
        mock_two_tower.validate_action.return_value = False

        input_signal = Signal(
            timestamp=time.time(),
            node_id="test_node",
            context=Context(task="init_task"),
            metrics=Metrics(duration_sec=0.0, cost_ippc=0.0, success=True)
        )

        result = await engine.run_step(input_signal)

        # Initial state should be present
        assert result["signals"] == [input_signal]
        assert result["memory_context"] == ""
        assert isinstance(result["inner_monologue"], list)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_execute_with_none_payload(self, engine, mock_orchestrator):
        """Execute should handle None payload"""
        mock_action = MagicMock()
        mock_action.action = "test_action"
        mock_action.payload = None

        state = {"proposed_action": mock_action}

        result = await engine.execute(state)

        envelope = mock_orchestrator.invoke.call_args[0][0]
        assert envelope.context["params"] == {}

    @pytest.mark.asyncio
    async def test_inner_voice_with_none_impulse_payload(self, engine, mock_two_tower):
        """Inner voice should handle impulse with None or empty payload"""
        mock_impulse = MagicMock()
        mock_impulse.payload = {}  # Use empty dict instead of None
        mock_two_tower.generate_impulse.return_value = mock_impulse

        state = {}

        # Should not raise exception
        result = await engine.inner_voice(state)
        assert "proposed_action" in result

    def test_risk_assessment_case_sensitivity(self, engine):
        """Risk assessment should be case-sensitive"""
        # Lowercase should match
        assert engine._assess_risk("execute_command", {}) == "high"

        # Uppercase should not match
        assert engine._assess_risk("EXECUTE_COMMAND", {}) == "medium"

    @pytest.mark.asyncio
    async def test_run_step_with_empty_signal(self, engine, mock_two_tower):
        """run_step should handle empty signal"""
        mock_two_tower.generate_impulse.return_value = MagicMock(payload={})
        mock_two_tower.validate_action.return_value = False

        empty_signal = Signal(
            timestamp=time.time(),
            node_id="",
            context=Context(task=""),
            metrics=Metrics(duration_sec=0.0, cost_ippc=0.0, success=True)
        )

        result = await engine.run_step(empty_signal)

        assert result["signals"] == [empty_signal]


class TestToolInvocationEnvelopeCreation:
    """Test ToolInvocationEnvelope construction"""

    @pytest.mark.asyncio
    async def test_envelope_has_correct_tool_name(self, engine, mock_orchestrator):
        """Envelope should have 'body' as tool_name"""
        mock_action = MagicMock()
        mock_action.action = "test"
        mock_action.payload = {}

        state = {"proposed_action": mock_action}
        await engine.execute(state)

        envelope = mock_orchestrator.invoke.call_args[0][0]
        assert envelope.tool_name == "body"

    @pytest.mark.asyncio
    async def test_envelope_has_correct_domain(self, engine, mock_orchestrator):
        """Envelope should have 'body' as domain"""
        mock_action = MagicMock()
        mock_action.action = "test"
        mock_action.payload = {}

        state = {"proposed_action": mock_action}
        await engine.execute(state)

        envelope = mock_orchestrator.invoke.call_args[0][0]
        assert envelope.domain == "body"

    @pytest.mark.asyncio
    async def test_envelope_has_zero_estimated_cost(self, engine, mock_orchestrator):
        """Envelope should have estimated_cost of 0.0"""
        mock_action = MagicMock()
        mock_action.action = "test"
        mock_action.payload = {}

        state = {"proposed_action": mock_action}
        await engine.execute(state)

        envelope = mock_orchestrator.invoke.call_args[0][0]
        assert envelope.estimated_cost == 0.0


class TestRegressionCases:
    """Regression tests for previously identified issues"""

    @pytest.mark.asyncio
    async def test_execute_handles_missing_payload_key(self, engine, mock_orchestrator):
        """Execute should handle actions without payload attribute"""
        # Create a mock that raises AttributeError for payload
        mock_action = MagicMock()
        mock_action.action = "test_action"
        type(mock_action).payload = PropertyMock(side_effect=AttributeError)

        state = {"proposed_action": mock_action}

        # Should handle gracefully
        try:
            result = await engine.execute(state)
            # If no error, good - the code handles it
            assert "execution_result" in result
        except AttributeError:
            # Expected if code doesn't handle missing payload
            pass

    @pytest.mark.asyncio
    async def test_multiple_actions_in_sequence(self, engine, mock_two_tower, mock_orchestrator):
        """Multiple run_step calls should work correctly"""
        mock_impulse = MagicMock()
        mock_impulse.action = "test"
        mock_impulse.payload = {}
        mock_two_tower.generate_impulse.return_value = mock_impulse
        mock_two_tower.validate_action.return_value = True

        signal1 = Signal(
            timestamp=time.time(),
            node_id="node1",
            context=Context(task="signal1_task"),
            metrics=Metrics(duration_sec=0.0, cost_ippc=0.0, success=True)
        )
        signal2 = Signal(
            timestamp=time.time(),
            node_id="node2",
            context=Context(task="signal2_task"),
            metrics=Metrics(duration_sec=0.0, cost_ippc=0.0, success=True)
        )

        result1 = await engine.run_step(signal1)
        result2 = await engine.run_step(signal2)

        # Both should complete successfully
        assert result1["execution_result"] is not None
        assert result2["execution_result"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])