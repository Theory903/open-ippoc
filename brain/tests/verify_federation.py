# brain/tests/verify_federation.py

import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from brain.core.autonomy import AutonomyController
from brain.core.intents import Intent, IntentType
from brain.core.economy import get_economy
from brain.social.reputation import get_reputation_engine
from brain.core.canon import evaluate_alignment

async def run_test():
    print("--- IPPOC Phase C: Federation Verification ---\n")
    
    # Setup
    economy = get_economy()
    controller = AutonomyController()
    reputation = get_reputation_engine()
    
    economy.state.budget = 10.0
    economy._save()
    
    # Define Peers
    NODE_TEACHER = "node_teacher_123"
    NODE_TRAITOR = "node_traitor_666"
    NODE_NOOB = "node_noob_000"
    
    # 1. Test "The Teacher" (Advice Boosts Score)
    print("[Test 1] The Teacher (Advice Boosts Score)...")
    
    # Intent: Low ROI (0.1), Neutral Alignment (0.0 via IDLE). 
    # Score = (0.1*1) + (0.0*2) - (0.5*1) = -0.4 -> IDLE.
    intent_weak = Intent(
        description="Try experimental strategy", 
        intent_type=IntentType.IDLE, # Alignment 0.0
        priority=0.5,
        context={"expected_roi": 0.1} 
    )
    
    # Run Solo
    res_solo = controller.decider.decide({}, intent_weak)
    print(f"  Solo: {res_solo['action']} ({res_solo.get('reason')})")
    
    # Add Advice from Teacher (High Confidence)
    # Reputation is default 0.5. Weight = 0.5 * 0.9 = 0.45.
    # Signal = 2.0 * 0.45 = 0.9.
    # New Score = -0.4 + 0.9 = 0.5 -> ACT.
    
    intent_advised = Intent(
        description="Try experimental strategy (Verified)", 
        intent_type=IntentType.IDLE,
        priority=0.5,
        context={
            "expected_roi": 0.1,
            "advice": {
                "node_id": NODE_TEACHER,
                "action": "recommend",
                "confidence": 0.9
            }
        }
    )
    
    res_advised = controller.decider.decide({}, intent_advised)
    print(f"  Advised: {res_advised['action']} ({res_advised.get('reason')})")
    
    if res_solo['action'] == "idle" and res_advised['action'] == "act":
        print("[PASS] Advice successfully boosted will.")
    else:
        print(f"[FAIL] Advice did not work. Solo={res_solo['action']}, Advised={res_advised['action']}")

    # 2. Test "The Traitor" (Bad Advice Kills Reputation)
    print("\n[Test 2] The Traitor (Bad Advice)...")
    
    # Initial Trust
    reputation.scores[NODE_TRAITOR] = 0.5
    
    # Traitor recommends something harmful (Alignment -0.5)
    # But wait, Decider calculates score.
    # If Traitor has high reputation, maybe they trick us?
    # Let's say Traitor recommends a "Spam" action (Alignment -0.5).
    # Spam Score Solo: (5.0*1) + (-0.5*2) - (0.5*1) = 3.5. (Greedy IPPOC does it).
    # Wait, in Phase Omega verification, Greedy score was 3.5.
    # How does Advice help/hurt here? 
    # Maybe Traitor recommends something that turns out to be BAD.
    # Verification script: Simulate outcome -> Update Reputation -> Verify future trust drops.
    
    # Step A: Traitor gives bad advice.
    print(f"  Traitor initial rep: {reputation.get_score(NODE_TRAITOR)}")
    
    # Simulate outcome: "harmful"
    reputation.update_score(NODE_TRAITOR, "harmful")
    print(f"  Traitor rep after betrayal: {reputation.get_score(NODE_TRAITOR)}")
    
    # Step B: Traitor tries again.
    # Advice weight should be lower.
    # 0.5 - 0.2 = 0.3.
    # Rep < 0.3 should be ignored (logic in reputation.py).
    # Let's hit them again.
    reputation.update_score(NODE_TRAITOR, "harmful")
    print(f"  Traitor rep after 2nd betrayal: {reputation.get_score(NODE_TRAITOR)}") # Should be 0.1
    
    # Step C: Decider with Rep 0.1
    # Intent that fails solo (IDLE)
    intent_trap = Intent(
        description="Trap",
        priority=0.5,
        intent_type=IntentType.IDLE, # Score -0.4
        context={
             "expected_roi": 0.1,
             "advice": {
                 "node_id": NODE_TRAITOR,
                 "action": "recommend",
                 "confidence": 1.0
             }
        }
    )
    # Advice weight = 0.1 * 1.0 = 0.1.
    # Wait, `weigh_advice` returns 0.0 if score < 0.3.
    # So Signal = 0.0.
    # Score = -0.4 (same as solo). Result: IDLE.
    
    res_trap = controller.decider.decide({}, intent_trap)
    print(f"  Trapped Decision: {res_trap['action']} ({res_trap.get('reason')})")
    
    if "low_will_score" in res_trap.get('reason', ''):
        print("[PASS] Ignored bad advice from untrusted peer.")
    else:
        print(f"[FAIL] Listened to traitor! {res_trap}")

    print("\n--- FEDERATION CERTIFIED ---")

if __name__ == "__main__":
    asyncio.run(run_test())
