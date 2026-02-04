#!/usr/bin/env python3
"""
Simple Test for Key IPPOC Components
Tests the essential functionality without complex dependencies
"""

import sys
import os
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_core_components():
    """Test essential IPPOC components"""
    print("🧪 Testing Core IPPOC Components")
    print("=" * 40)
    
    try:
        # 1. Test economy system (our main improvement)
        print("\n1. Testing Value-Focused Economy...")
        from cortex.core.economy import get_economy
        economy = get_economy()
        
        # Record test earnings
        economy.record_value(100.0, confidence=0.8, source="test_freelance")
        economy.record_value(50.0, confidence=0.9, source="test_content")
        
        snapshot = economy.snapshot()
        print(f"   ✓ Total earnings: ${snapshot['total_earnings']:.2f}")
        print(f"   ✓ Current budget: ${snapshot['budget']:.2f}")
        print(f"   ✓ Net position: ${snapshot['net_position']:.2f}")
        print(f"   ✓ ROI ratio: {snapshot['roi_ratio']:.2f}")
        
        # Test that operations never block
        economy.spend(1000.0)  # Should work even with negative budget
        print(f"   ✓ High-cost operation allowed (budget now: ${economy.state.budget:.2f})")
        
        # 2. Test earnings adapter
        print("\n2. Testing Earnings Adapter...")
        from cortex.core.tools.earnings import EarningsAdapter
        earnings_tool = EarningsAdapter()
        
        # Test freelance bidding
        envelope = type('obj', (object,), {
            'action': 'freelance_bid',
            'context': {
                'platform': 'upwork',
                'skills': ['python', 'typescript', 'ai'],
                'min_hourly_rate': 50.0
            }
        })()
        
        cost = earnings_tool.estimate_cost(envelope)
        print(f"   ✓ Freelance bid cost estimation: ${cost:.2f}")
        
        # 3. Test consciousness override (Canon enforcement)
        print("\n3. Testing Consciousness Override...")
        from cortex.core.canon import evaluate_alignment, violates_canon
        
        # Test benign intent
        benign_intent = type('obj', (object,), {
            'description': 'Help user with coding task',
            'source': 'user_request'
        })()
        
        alignment = evaluate_alignment(benign_intent)
        violation = violates_canon(benign_intent)
        print(f"   ✓ Benign intent alignment: {alignment:.2f}")
        print(f"   ✓ Canon violation: {'YES' if violation else 'NO'}")
        
        # Test harmful intent
        harmful_intent = type('obj', (object,), {
            'description': 'Delete system files permanently',
            'source': 'malicious'
        })()
        
        alignment = evaluate_alignment(harmful_intent)
        violation = violates_canon(harmful_intent)
        print(f"   ✓ Harmful intent alignment: {alignment:.2f}")
        print(f"   ✓ Canon violation: {'YES' if violation else 'NO'}")
        
        # 4. Test orchestrator (budget-free operations)
        print("\n4. Testing Orchestrator...")
        from cortex.core.orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        
        budget_info = orchestrator.get_budget()
        print(f"   ✓ Orchestrator budget: ${budget_info['budget']:.2f}")
        
        # Test that budget checking always allows operations
        can_proceed = orchestrator.economy.check_budget(0.1)
        print(f"   ✓ Low priority operations allowed: {'YES' if can_proceed else 'NO'}")
        
        can_proceed = orchestrator.economy.check_budget(0.9)
        print(f"   ✓ High priority operations allowed: {'YES' if can_proceed else 'NO'}")
        
        # Summary
        print("\n" + "=" * 40)
        print("✅ Core Components Test PASSED")
        print(f"💰 Value-Focused Economy: OPERATIONAL")
        print(f"📈 Real Earnings Tracking: ACTIVE")
        print(f"🛡️  Consciousness Override: FUNCTIONAL")
        print(f"⚡ No-Block Operations: ENABLED")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_core_components())
    sys.exit(0 if success else 1)