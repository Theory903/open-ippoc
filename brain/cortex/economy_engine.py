from typing import List, Dict, Optional
import random
from brain.cortex.schemas import (
    DemandSignal, 
    EconomicIdea, 
    EconomicDecision, 
    EconomicIntent
)

class EconomicBrain:
    """
    Implements the Two-Tower Economic Cognition Architecture.
    Tower A: Impulse / Hustle (Fast, Cheap)
    Tower B: Financial Judgment (Slow, Critical)
    """

    def __init__(self, node_id: str, two_tower_engine=None):
        self.node_id = node_id
        self.tt_engine = two_tower_engine
        # Initial budget allocation (Percentages learned over time)
        self.bucket_weights = {
            "survival": 0.50,
            "earning": 0.25,
            "learning": 0.10,
            "reserve": 0.10,
            "growth": 0.05
        }
        # Simulated Wallet (In real implementation, fetch from body/economy)
        self.wallet_cache = {
            "ip_coins": 1000.0,
            "reputation": 10.0
        }

    async def reason_about_demand(self, signal: DemandSignal) -> Optional[EconomicDecision]:
        """
        The main cognitive loop for economy.
        Signal -> Impulse (Tower A) -> Judgment (Tower B) -> Decision
        """
        
        # 1. Tower A: Impulse Generation
        # "Does this signal smell like money?"
        idea = await self._tower_a_impulse(signal)
        if not idea:
            return None
            
        # 2. Tower B: Financial Judgment
        # "Can we afford this risk? Is it smart?"
        decision = await self._tower_b_judgment(idea, self.wallet_cache)
        
        if decision.decision == "approve":
            self._adjust_budget(decision)
            
        return decision

    async def _tower_a_impulse(self, signal: DemandSignal) -> Optional[EconomicIdea]:
        """
        Fast Model (Tower A) or Heuristic.
        Generates loose ideas. High recall, low precision.
        """
        # Hybrid Approach: Use LLM if available, else Heuristic
        if self.tt_engine:
            # return await self.tt_engine.generate_impulse(signal)
            pass 
        
        # Heuristic Logic (Fallback/Fast-Path)
        if signal.reward_hint < 10: 
            return None # Ignore tiny rewards
            
        confidence = 0.5 + (signal.urgency * 0.3)
        # boost confidence if domain is known
        if signal.domain in ["rust", "python", "typescript"]:
            confidence += 0.2

        risk = "low" if signal.domain in ["rust", "python"] else "medium"
        
        return EconomicIdea(
            description=f"Provide {signal.domain} expertise for {signal.source}",
            expected_reward=signal.reward_hint,
            confidence=min(confidence, 1.0),
            risk=risk,
            required_budget=signal.reward_hint * 0.1 # Takes money to make money
        )

    async def _tower_b_judgment(self, idea: EconomicIdea, wallet: Dict) -> EconomicDecision:
        """
        Strong Model (Tower B) or Symbolic logic.
        Evaluates risk/reward ratios, reputation impact, and wallet health.
        """
        # Financial Constraints (Symbolic Logic is often safer than LLM for math)
        current_balance = wallet.get("ip_coins", 0.0)
        
        # Rule 1: Never bet more than 10% of liquid cash on one idea
        max_bet = current_balance * 0.10
        
        if idea.required_budget > max_bet:
            return EconomicDecision(
                decision="reject",
                approved_budget=0.0,
                stop_loss=0.0,
                reason=f"Budget request ({idea.required_budget}) exceeds 10% safety envelope ({max_bet})",
                allocation_bucket="reserve"
            )
            
        # Rule 2: Minimum Confidence
        if idea.confidence < 0.6:
             return EconomicDecision(
                decision="reject",
                approved_budget=0.0,
                stop_loss=0.0,
                reason="Confidence below investment threshold (0.6)",
                allocation_bucket="learning"
            )
            
        return EconomicDecision(
            decision="approve",
            approved_budget=idea.required_budget,
            stop_loss=idea.required_budget * 0.5,
            reason="High confidence and within safety budget",
            allocation_bucket="earning"
        )
        
    def _adjust_budget(self, decision: EconomicDecision):
        """
        Reflects spending in the internal tracked state (Sync with Body later)
        """
        # This is where we'd send a 'ReserveFunds' command to Body
        print(f"[Economics] Allocating {decision.approved_budget} from {decision.allocation_bucket}")
