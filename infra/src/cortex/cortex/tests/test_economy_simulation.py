import pytest
import asyncio
from cortex.cortex.schemas import DemandSignal
from cortex.cortex.economy_engine import EconomicBrain

@pytest.mark.asyncio
async def test_economic_reasoning_flow():
    """
    Verifies that a DemandSignal triggers the full Two-Tower loop.
    """
    brain = EconomicBrain(node_id="test-node-001")
    
    # 1. Simulate a High-Value Demand Signal
    signal = DemandSignal(
        domain="rust",
        urgency=0.8,
        reward_hint=100.0, # High enough to trigger impulse
        source="swarm_chat"
    )
    
    print(f"\n[Test] Injecting Signal: {signal}")
    
    # 2. Run Reasoning
    decision = await cortex.reason_about_demand(signal)
    
    # 3. Verify Outcome
    assert decision is not None
    print(f"[Test] Decision: {decision}")
    
    assert decision.decision == "approve"
    # Budget check: 10% of 1000 = 100. Cost = 10% of 100 = 10.
    # 10 < 100, so it should be approved.
    assert decision.approved_budget == 10.0
    assert decision.allocation_bucket == "earning"

@pytest.mark.asyncio
async def test_economic_rejection_low_value():
    """
    Verifies that low-value signals are ignored by Tower A.
    """
    brain = EconomicBrain(node_id="test-node-001")
    
    signal = DemandSignal(
        domain="python",
        urgency=0.1,
        reward_hint=5.0, # Too low per policy (< 10)
        source="noise"
    )
    
    decision = await cortex.reason_about_demand(signal)
    assert decision is None # Should be filtered by Tower A

@pytest.mark.asyncio
async def test_economic_rejection_high_risk():
    """
    Verifies that high-cost ideas are rejected by Tower B.
    """
    brain = EconomicBrain(node_id="test-node-001")
    
    # Signal asking for huge investment
    signal = DemandSignal(
        domain="crypto_speculation",
        urgency=1.0,
        reward_hint=5000.0, # Requires 500 budget
        source="scam"
    )
    
    # Max bet is 10% of 1000 = 100.
    # Required budget = 500.
    # Should be rejected.
    
    decision = await cortex.reason_about_demand(signal)
    
    assert decision is not None # Tower A might like it (high reward)
    print(f"[Test] Risky Decision: {decision}")
    
    assert decision.decision == "reject"
    assert decision.allocation_bucket == "reserve"
    assert "exceeds" in decision.reason
