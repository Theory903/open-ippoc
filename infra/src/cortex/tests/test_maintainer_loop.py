# brain/tests/test_maintainer_loop.py

import pytest
from cortex.maintainer.types import SignalSummary, PainScore, MentorAdvice
from cortex.maintainer.pain import score_pain
from cortex.maintainer.evolution_loop import maybe_evolve
from cortex.core.bootstrap import bootstrap_tools

# --- Stub Data ---
def get_high_pain_signals():
    # Force high pain: many errors, high cost
    return SignalSummary(
        errors_last_hour=10,
        avg_cost=5.0,
        success_rate=0.5
    )

def get_low_pain_signals():
    # Force zen mode
    return SignalSummary(
        errors_last_hour=0,
        avg_cost=0.5,
        success_rate=1.0
    )

def test_pain_scoring():
    high = get_high_pain_signals()
    pain_h = score_pain(high)
    assert pain_h.upgrade_pressure > 0.5
    assert "economy" in pain_h.domains_in_pain
    
    low = get_low_pain_signals()
    pain_l = score_pain(low)
    assert pain_l.upgrade_pressure < 0.2

def test_maintainer_decision_making():
    # We need to bootstrap tools because maybe_evolve calls get_orchestrator().register
    # Actually, we should just bootstrap once globally for the test session usually,
    # but here calling it is safe as Singleton handles re-init checks (mostly).
    bootstrap_tools()
    
    from cortex.core.orchestrator import get_orchestrator
    
    # 1. High Pain Scenario -> Should trigger Evolution Tool Call
    # We mock the orchestrator.invoke to spy on it
    orc = get_orchestrator()
    original_invoke = orc.invoke
    
    calls = []
    def mock_invoke(envelope):
        calls.append(envelope)
        from cortex.core.tools.base import ToolResult
        return ToolResult(success=True, output="Mocked Proposal", cost_spent=1.0)
    
    orc.invoke = mock_invoke
    
    # Run loop with high pain
    high_sigs = get_high_pain_signals()
    pain_h = score_pain(high_sigs)
    maybe_evolve(pain_h, high_sigs)
    
    # Verify call happened
    assert len(calls) > 0
    # Check if 'evolution' tool was called
    assert any(c.tool_name == "evolution" and c.action == "propose_patch" for c in calls)
    
    # 2. Low Pain Scenario -> Should trigger nothing (or just memory log)
    calls.clear()
    low_sigs = get_low_pain_signals()
    pain_l = score_pain(low_sigs)
    maybe_evolve(pain_l, low_sigs)
    
    # Verify NO evolution call happened
    assert not any(c.tool_name == "evolution" for c in calls)
    
    # Restore
    orc.invoke = original_invoke

if __name__ == "__main__":
    try:
        test_pain_scoring()
        print("✅ Pain Scoring Logic Passed")
        test_maintainer_decision_making()
        print("✅ Evolution Logic Passed")
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
