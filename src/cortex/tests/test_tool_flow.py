# brain/tests/test_tool_flow.py

import pytest
from cortex.core.orchestrator import get_orchestrator
from cortex.core.tools.base import ToolInvocationEnvelope
from cortex.core.bootstrap import bootstrap_tools
from cortex.core.exceptions import ToolExecutionError, BudgetExceeded
# We'll mock the actual Adapter execute methods to avoid network calls during unit test

def test_tool_registration():
    bootstrap_tools()
    orc = get_orchestrator()
    assert "memory" in orc.tools
    assert "body" in orc.tools
    assert "evolution" in orc.tools
    assert "research" in orc.tools
    assert "simulation" in orc.tools

def test_new_domains_invocation():
    # Helper to test new adapters
    orc = get_orchestrator()
    
    # Research Tool (Cerebellum)
    env_res = ToolInvocationEnvelope(
        tool_name="research",
        domain="cognition",
        action="digest_paper",
        context={"url": "http://arxiv.org/pdf/1234.pdf"},
        estimated_cost=2.0
    )
    res_res = orc.invoke(env_res)
    assert res_res.success
    assert res_res.cost_spent == 2.0
    
    # Simulation Tool (WorldModel)
    env_sim = ToolInvocationEnvelope(
        tool_name="simulation",
        domain="simulation",
        action="simulate_action",
        context={"action_to_simulate": "deploy_update"},
        estimated_cost=1.5
    )
    res_sim = orc.invoke(env_sim)
    assert res_sim.success
    assert "85%" in str(res_sim.output)

def test_invocation_flow():
    orc = get_orchestrator()
    
    # Mocking memory execution for test safety
    memory_tool = orc.tools["memory"]
    original_execute = memory_tool._async_execute
    
    async def mock_execute(envelope):
        from cortex.core.tools.base import ToolResult
        return ToolResult(success=True, output="Mocked Memory Success", cost_spent=0.5)
    
    memory_tool._async_execute = mock_execute
    
    envelope = ToolInvocationEnvelope(
        tool_name="memory",
        domain="memory",
        action="store_episodic",
        context={"content": "Test memory"},
        risk_level="low"
    )
    
    result = orc.invoke(envelope)
    assert result.success is True
    assert result.output == "Mocked Memory Success"
    
    # Restore
    memory_tool._async_execute = original_execute

def test_orchestrator_guards():
    orc = get_orchestrator()
    
    # Test Unregistered Tool
    env_bad = ToolInvocationEnvelope(
        tool_name="fake_tool",
        domain="body",
        action="explode",
        estimated_cost=0
    )
    
    with pytest.raises(ToolExecutionError) as excinfo:
        orc.invoke(env_bad)
    assert "Tool not registered" in str(excinfo.value)

def test_budget_enforcement():
    orc = get_orchestrator()
    orc.current_budget = 0.1
    
    envelope = ToolInvocationEnvelope(
        tool_name="evolution", # Cost 5.0
        domain="evolution",
        action="propose_patch",
        context={"environment": "sandbox", "diff": "test"},
        estimated_cost=5.0
    )
    
    with pytest.raises(BudgetExceeded):
        orc.invoke(envelope)

if __name__ == "__main__":
    # verification script style
    try:
        test_tool_registration()
        print("✅ Registration Test Passed (All Domains)")
        test_new_domains_invocation()
        print("✅ New Domains (Research/Sim) Passed")
        test_invocation_flow()
        print("✅ Invocation Flow Passed")
        test_orchestrator_guards()
        print("✅ Guards Test Passed")
        try:
             test_budget_enforcement()
             print("✅ Budget Test Passed")
        except Exception as e:
            print(f"❌ Budget Test Failed: {e}")
            
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
