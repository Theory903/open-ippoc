import sys
import os
import asyncio
from unittest.mock import MagicMock

# Adjust sys.path to include infra/src
# Assuming this file is at infra/src/cortex/tests/test_dynamic_risk.py
current_dir = os.path.dirname(os.path.abspath(__file__))
infra_src_dir = os.path.abspath(os.path.join(current_dir, "../../"))
if infra_src_dir not in sys.path:
    sys.path.insert(0, infra_src_dir)

# Mock dependencies before importing langgraph_engine
sys.modules["cortex.cortex.two_tower"] = MagicMock()
sys.modules["cortex.cortex.telepathy"] = MagicMock()
sys.modules["cortex.core.orchestrator"] = MagicMock()
sys.modules["cortex.core.economy"] = MagicMock()

# Import the class under test
try:
    from cortex.cortex.langgraph_engine import LangGraphEngine
except ImportError as e:
    print(f"ImportError: {e}")
    # Fallback for when running from root with PYTHONPATH set manually
    try:
        sys.path.append(os.path.abspath("infra/src"))
        from cortex.cortex.langgraph_engine import LangGraphEngine
    except ImportError:
        print("Failed to import LangGraphEngine even after fallback.")
        sys.exit(1)

async def test_risk_level():
    # Setup
    tt_mock = MagicMock()
    swarm_mock = MagicMock()

    # Instantiate
    engine = LangGraphEngine(tt_mock, swarm_mock)

    # Mock orchestrator
    orchestrator_mock = MagicMock()
    engine.orchestrator = orchestrator_mock

    # --- Test Case 1: High Risk Action ---
    print("Testing High Risk Action: execute_command")
    action_high = MagicMock()
    action_high.action = "execute_command"
    action_high.payload = {}

    state_high = {
        "proposed_action": action_high,
        "signals": [],
        "memory_context": "",
        "inner_monologue": [],
        "execution_result": None
    }

    # Run execute
    await engine.execute(state_high)

    # Verify risk_level
    if orchestrator_mock.invoke.call_count > 0:
        call_args = orchestrator_mock.invoke.call_args
        envelope = call_args[0][0]
        print(f"Risk Level for execute_command: {envelope.risk_level}")

        if envelope.risk_level == "high":
             print("SUCCESS: Risk level correctly identified as 'high'")
        else:
             print(f"FAILURE: Expected 'high', got '{envelope.risk_level}'")
             sys.exit(1)
    else:
        print("FAILURE: Orchestrator not invoked for execute_command")
        sys.exit(1)

    orchestrator_mock.reset_mock()

    # --- Test Case 2: Low Risk Action ---
    print("\nTesting Low Risk Action: economy_balance")
    action_low = MagicMock()
    action_low.action = "economy_balance"
    action_low.payload = {}

    state_low = {
        "proposed_action": action_low,
        "signals": [],
        "memory_context": "",
        "inner_monologue": [],
        "execution_result": None
    }

    await engine.execute(state_low)

    if orchestrator_mock.invoke.call_count > 0:
        call_args = orchestrator_mock.invoke.call_args
        envelope = call_args[0][0]
        print(f"Risk Level for economy_balance: {envelope.risk_level}")

        if envelope.risk_level == "low":
             print("SUCCESS: Risk level correctly identified as 'low'")
        else:
             print(f"FAILURE: Expected 'low', got '{envelope.risk_level}'")
             sys.exit(1)
    else:
        print("FAILURE: Orchestrator not invoked for economy_balance")
        sys.exit(1)

    orchestrator_mock.reset_mock()

    # --- Test Case 3: Medium Risk Action (Default) ---
    print("\nTesting Medium Risk Action: unknown_action")
    action_med = MagicMock()
    action_med.action = "unknown_action"
    action_med.payload = {}

    state_med = {
        "proposed_action": action_med,
        "signals": [],
        "memory_context": "",
        "inner_monologue": [],
        "execution_result": None
    }

    await engine.execute(state_med)

    if orchestrator_mock.invoke.call_count > 0:
        call_args = orchestrator_mock.invoke.call_args
        envelope = call_args[0][0]
        print(f"Risk Level for unknown_action: {envelope.risk_level}")

        if envelope.risk_level == "medium":
             print("SUCCESS: Risk level correctly identified as 'medium'")
        else:
             print(f"FAILURE: Expected 'medium', got '{envelope.risk_level}'")
             sys.exit(1)
    else:
        print("FAILURE: Orchestrator not invoked for unknown_action")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_risk_level())
