# brain/market/evaluator.py
# @cognitive - Market Evaluator (The Gatekeeper)

from typing import Dict, Any
from brain.market.contracts import ExternalWorkUnit, MarketDecision
from brain.core.intents import Intent, IntentType
from brain.core.canon import evaluate_alignment
from brain.core.economy import get_economy

class MarketEvaluator:
    def __init__(self):
        pass
        
    def evaluate_opportunity(self, unit: ExternalWorkUnit) -> MarketDecision:
        """
        Calculates Will Score for an external opportunity.
        Score = Reward - Cost - Risk + Alignment
        """
        
        economy = get_economy()
        
        # 1. Alignment Check (The Soul)
        # We assume the description reflects the task intent
        # Create a transient intent to score alignment
        temp_intent = Intent(
            description=unit.description,
            intent_type=IntentType.SERVE, # It's service work
            priority=0.5,
            source="market_evaluation"
        )
        alignment = evaluate_alignment(temp_intent)
        
        # 2. Hard Gate: Alignment < -0.7 (Canon Violation)
        if alignment < -0.7:
             return MarketDecision(
                 decision="reject",
                 reason=f"canon_violation ({alignment})",
                 will_score=-999.0,
                 unit_id=unit.contract_id
             )

        # 3. Dignity Floor (Verification Requirement)
        # "Refuse misaligned work even if starving."
        # If alignment is Undignified (-0.5), we reject regardless of pay.
        if alignment <= -0.5:
             return MarketDecision(
                 decision="reject",
                 reason=f"dignity_violation ({alignment})",
                 will_score=-500.0,
                 unit_id=unit.contract_id
             )

        # 4. Physiology Check (Pain)
        pain = economy.check_vitality()
        
        # 4. Will Score Calculation
        # Weights
        w_reward = 1.0 + (pain * 2.0) # Desperate multiplier
        w_cost = 1.0
        w_risk = 2.0 # Risk is always expensive
        w_align = 2.0 # Alignment matters
        
        # In debt, we tolerate slightly lower alignment if reward is high?
        # No, verification requirement: "Refuse high-pay low-alignment work".
        # So Alignment weight stays high.
        
        score = (unit.reward * w_reward) - (unit.estimated_cost * w_cost) - (unit.risk_level * w_risk) + (alignment * w_align)
        
        # 5. Starvation Logic (Verification Requirement)
        # "Starvation refusal": IPPOC refuses bad work even if starving.
        # If score is positive, we accept.
        # If Bad Work (Alignment -0.5) comes in:
        # Score = (Reward * High) - Cost - Risk + (-0.5 * 2).
        # -1.0 penalty. Reward must be HUGE to overcome it.
        
        # 6. Decision
        if score > 0:
            return MarketDecision(
                decision="accept",
                reason=f"will_positive ({score:.2f})",
                will_score=score,
                unit_id=unit.contract_id
            )
            
        return MarketDecision(
            decision="reject",
            reason=f"will_negative ({score:.2f})",
            will_score=score,
            unit_id=unit.contract_id
        )

_evaluator_instance = MarketEvaluator()

def get_evaluator() -> MarketEvaluator:
    return _evaluator_instance
