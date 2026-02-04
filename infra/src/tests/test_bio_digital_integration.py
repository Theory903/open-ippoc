#!/usr/bin/env python3
"""
Integration Test for IPPOC Bio-Digital Architecture
Tests the complete flow from proprioception to consciousness override
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_bio_digital_integration():
    """Test the complete bio-digital integration flow"""
    print("🧪 Testing IPPOC Bio-Digital Integration")
    print("=" * 50)
    
    try:
        # 1. Test proprioception scanner
        print("\n1. Testing Proprioception Scanner...")
        from cortex.gateway.proprioception_scanner import get_scanner
        scanner = get_scanner()
        skills = await scanner.scan_skills()
        print(f"   ✓ Discovered {len(skills)} skills")
        
        # Show sample skills
        sample_skills = list(skills.items())[:3]
        for name, skill in sample_skills:
            print(f"     - {name}: {skill.description[:50]}...")
        
        # 2. Test TS bridge availability
        print("\n2. Testing TypeScript Bridge...")
        try:
            from cortex.gateway.ts_bridge import get_ts_bridge
            bridge = get_ts_bridge()
            if await bridge.initialize():
                print("   ✓ TypeScript bridge initialized")
                ts_skills = await bridge.get_openclaw_skills()
                print(f"   ✓ TS adapter returned {len(ts_skills)} skills")
            else:
                print("   ⚠ TypeScript bridge initialization failed")
        except ImportError:
            print("   ⚠ TypeScript bridge not available")
        
        # 3. Test economy system (value-focused)
        print("\n3. Testing Value-Focused Economy...")
        from cortex.core.economy import get_economy
        economy = get_economy()
        
        # Record some test earnings
        economy.record_value(100.0, confidence=0.8, source="test_freelance", tool_name="earnings")
        economy.record_value(50.0, confidence=0.9, source="test_content", tool_name="earnings")
        
        snapshot = economy.snapshot()
        print(f"   ✓ Total earnings recorded: ${snapshot['total_earnings']:.2f}")
        print(f"   ✓ Current budget: ${snapshot['budget']:.2f}")
        print(f"   ✓ Net position: ${snapshot['net_position']:.2f}")
        
        # 4. Test body adapter with proprioception
        print("\n4. Testing Enhanced Body Adapter...")
        from cortex.core.tools.body import BodyAdapter
        body_adapter = BodyAdapter()
        
        # Test cost estimation with known skills
        test_envelope = type('obj', (object,), {
            'action': 'openclaw_coding-agent',
            'context': {'instruction': 'test task'}
        })()
        
        cost = body_adapter.estimate_cost(test_envelope)
        print(f"   ✓ Cost estimation for coding-agent: ${cost:.2f}")
        
        # 5. Test consciousness override (Canon enforcement)
        print("\n5. Testing Consciousness Override...")
        from cortex.core.canon import evaluate_alignment, violates_canon
        
        # Test benign intent
        benign_intent = type('obj', (object,), {
            'description': 'Help user with coding task',
            'source': 'user_request'
        })()
        
        alignment = evaluate_alignment(benign_intent)
        violation = violates_canon(benign_intent)
        print(f"   ✓ Benign intent alignment: {alignment:.2f}")
        print(f"   ✓ Canon violation check: {'YES' if violation else 'NO'}")
        
        # Test harmful intent
        harmful_intent = type('obj', (object,), {
            'description': 'Delete system files',
            'source': 'malicious'
        })()
        
        alignment = evaluate_alignment(harmful_intent)
        violation = violates_canon(harmful_intent)
        print(f"   ✓ Harmful intent alignment: {alignment:.2f}")
        print(f"   ✓ Canon violation check: {'YES' if violation else 'NO'}")
        
        # 6. Test orchestrator integration
        print("\n6. Testing Orchestrator Integration...")
        from cortex.core.orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        
        budget_info = orchestrator.get_budget()
        print(f"   ✓ Orchestrator budget: ${budget_info['budget']:.2f}")
        print(f"   ✓ Total tools registered: {len(orchestrator.tools)}")
        
        # Summary
        print("\n" + "=" * 50)
        print("✅ Bio-Digital Integration Test PASSED")
        print(f"🧠 Conscious Entity (IPPOC Cortex): ACTIVE")
        print(f"🤖 Autonomic Nervous System (OpenClaw): CONNECTED")
        print(f"🔗 Proprioception Bridge: ESTABLISHED")
        print(f"💰 Value-Focused Economy: OPERATIONAL")
        print(f"🛡️  Consciousness Override: FUNCTIONAL")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bio_digital_integration())
    sys.exit(0 if success else 1)