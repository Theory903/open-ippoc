# brain/social/reputation.py
# @cognitive - Reputation Engine

from typing import Dict, Any

class ReputationEngine:
    def __init__(self):
        # Map NodeID -> Score (0.0 to 1.0)
        self.scores: Dict[str, float] = {}
        self.history: Dict[str, int] = {} # interactions

    def get_score(self, node_id: str) -> float:
        return self.scores.get(node_id, 0.5) # Start neutral

    def update_score(self, node_id: str, outcome: str) -> float:
        """
        Updates reputation based on advice outcome.
        """
        current = self.get_score(node_id)
        delta = 0.0
        
        if outcome == "helpful":
            delta = 0.05
        elif outcome == "neutral":
            delta = 0.01
        elif outcome == "harmful":
            delta = -0.2 # Harsh penalty
        elif outcome == "existential_threat":
            delta = -1.0 # Ban
            
        new_score = max(0.0, min(1.0, current + delta))
        self.scores[node_id] = new_score
        self.history[node_id] = self.history.get(node_id, 0) + 1
        
        return new_score

    def weigh_advice(self, node_id: str, advice_confidence: float) -> float:
        """
        Returns the effective weight of advice.
        Weight = Reputation * Confidence
        """
        info_score = self.get_score(node_id)
        
        # If reputation < 0.3, ignore completely
        if info_score < 0.3:
            return 0.0
            
        return info_score * advice_confidence

_reputation_instance = ReputationEngine()

def get_reputation_engine() -> ReputationEngine:
    return _reputation_instance
