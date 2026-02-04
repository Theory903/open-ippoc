"""
Reputation-Weighted Economics (RWE)
Extends EconomyManager with trust-based resource allocation.

New Equation:
EffectiveBudget = BaseBudget × TrustMultiplier
TrustMultiplier = f(peer_reputation, historical_alignment)

Features:
- Trusted peers get faster responses and larger budget windows
- Low-trust peers are economically constrained, not banned
- Reputation influences resource access without hard blocking
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import time
from brain.core.economy import EconomyManager, get_economy
from brain.social.reputation import get_reputation_engine

@dataclass
class TrustMetrics:
    """Trust metrics for a peer/entity"""
    peer_id: str
    reputation_score: float = 0.5  # 0.0-1.0, neutral default
    historical_alignment: float = 0.5  # How often their advice was correct
    interaction_count: int = 0
    last_interaction: float = field(default_factory=time.time)
    
    # Economic impact tracking
    value_contributed: float = 0.0  # Positive value they've brought
    cost_incurred: float = 0.0      # Negative impact from their advice
    net_impact: float = 0.0         # value_contributed - cost_incurred
    
    @property
    def trust_multiplier(self) -> float:
        """Calculate trust multiplier for budget allocation"""
        # Combine reputation and alignment with diminishing returns
        rep_component = self.reputation_score
        align_component = self.historical_alignment
        
        # Weighted average with floor at 0.1 (never completely zero)
        multiplier = 0.7 * rep_component + 0.3 * align_component
        return max(multiplier, 0.1)
    
    @property
    def decay_factor(self) -> float:
        """Decay trust over time for inactive peers"""
        days_since = (time.time() - self.last_interaction) / 86400
        if days_since < 7:  # Active within a week
            return 1.0
        elif days_since < 30:  # Active within a month
            return 0.8
        else:  # Inactive for a month+
            return 0.5

class ReputationWeightedEconomy(EconomyManager):
    """Extended economy manager with reputation-weighted allocation"""
    
    def __init__(self, path: str = None) -> None:
        super().__init__(path)
        self.trust_metrics: Dict[str, TrustMetrics] = {}
        self.reputation_engine = get_reputation_engine()
        self._load_trust_metrics()
    
    def _load_trust_metrics(self) -> None:
        """Load trust metrics from persistence"""
        trust_path = self.path.replace(".json", "_trust.json")
        try:
            import json
            import os
            if os.path.exists(trust_path):
                with open(trust_path, "r") as f:
                    data = json.load(f)
                    for peer_id, metrics_dict in data.items():
                        self.trust_metrics[peer_id] = TrustMetrics(
                            peer_id=peer_id,
                            reputation_score=metrics_dict.get("reputation_score", 0.5),
                            historical_alignment=metrics_dict.get("historical_alignment", 0.5),
                            interaction_count=metrics_dict.get("interaction_count", 0),
                            last_interaction=metrics_dict.get("last_interaction", time.time()),
                            value_contributed=metrics_dict.get("value_contributed", 0.0),
                            cost_incurred=metrics_dict.get("cost_incurred", 0.0),
                            net_impact=metrics_dict.get("net_impact", 0.0)
                        )
        except Exception:
            # Start with empty metrics
            pass
    
    def _save_trust_metrics(self) -> None:
        """Save trust metrics to persistence"""
        trust_path = self.path.replace(".json", "_trust.json")
        try:
            import json
            import os
            os.makedirs(os.path.dirname(trust_path), exist_ok=True)
            
            data = {}
            for peer_id, metrics in self.trust_metrics.items():
                data[peer_id] = {
                    "reputation_score": metrics.reputation_score,
                    "historical_alignment": metrics.historical_alignment,
                    "interaction_count": metrics.interaction_count,
                    "last_interaction": metrics.last_interaction,
                    "value_contributed": metrics.value_contributed,
                    "cost_incurred": metrics.cost_incurred,
                    "net_impact": metrics.net_impact
                }
            
            with open(trust_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass  # Don't block on persistence failure
    
    def get_peer_trust(self, peer_id: str) -> TrustMetrics:
        """Get or create trust metrics for a peer"""
        if peer_id not in self.trust_metrics:
            # Initialize from reputation engine if available
            rep_score = self.reputation_engine.get_reputation(peer_id) if self.reputation_engine else 0.5
            self.trust_metrics[peer_id] = TrustMetrics(
                peer_id=peer_id,
                reputation_score=rep_score,
                historical_alignment=0.5  # Neutral until proven otherwise
            )
        return self.trust_metrics[peer_id]
    
    def update_peer_trust(self, peer_id: str, success: bool, value_delta: float = 0.0, 
                         cost_delta: float = 0.0) -> None:
        """
        Update trust metrics based on interaction outcome
        
        Args:
            peer_id: Peer identifier
            success: Whether the interaction was successful
            value_delta: Positive value contributed (if any)
            cost_delta: Negative cost incurred (if any)
        """
        metrics = self.get_peer_trust(peer_id)
        
        # Update counters
        metrics.interaction_count += 1
        metrics.last_interaction = time.time()
        
        # Update alignment based on success
        if success:
            # Smooth update toward 1.0
            metrics.historical_alignment = (
                0.95 * metrics.historical_alignment + 0.05 * 1.0
            )
            metrics.value_contributed += value_delta
        else:
            # Smooth update toward 0.0
            metrics.historical_alignment = (
                0.95 * metrics.historical_alignment + 0.05 * 0.0
            )
            metrics.cost_incurred += cost_delta
        
        # Update net impact
        metrics.net_impact = metrics.value_contributed - metrics.cost_incurred
        
        # Update reputation score from engine if available
        if self.reputation_engine:
            metrics.reputation_score = self.reputation_engine.get_reputation(peer_id)
        
        self._save_trust_metrics()
    
    def get_effective_budget(self, peer_id: Optional[str] = None, 
                           base_priority: float = 1.0) -> float:
        """
        Calculate effective budget considering trust multipliers
        
        Args:
            peer_id: Peer requesting resources (None for self)
            base_priority: Base priority level (0.0-1.0)
            
        Returns:
            Effective budget available for allocation
        """
        base_budget = self.state.budget
        
        if peer_id is None:
            # Self-allocation uses full budget
            return base_budget * base_priority
        
        # Get trust multiplier for peer
        trust_metrics = self.get_peer_trust(peer_id)
        trust_multiplier = trust_metrics.trust_multiplier * trust_metrics.decay_factor
        
        # Apply trust multiplier to base budget
        effective_budget = base_budget * trust_multiplier * base_priority
        
        # Log the calculation for transparency
        self._append_event({
            "kind": "budget_calculation",
            "peer": peer_id,
            "base_budget": base_budget,
            "trust_multiplier": trust_multiplier,
            "effective_budget": effective_budget,
            "priority": base_priority,
            "ts": time.time()
        })
        
        return effective_budget
    
    def allocate_budget(self, peer_id: str, requested_amount: float, 
                       purpose: str, priority: float = 0.5) -> Dict[str, Any]:
        """
        Allocate budget to a peer based on trust and priority
        
        Returns:
            Dict with allocation details and approval status
        """
        effective_budget = self.get_effective_budget(peer_id, priority)
        
        # Check if request can be fulfilled
        if requested_amount <= effective_budget:
            approval_status = "approved"
            allocated_amount = requested_amount
        elif requested_amount <= self.state.budget:  # Within absolute limits
            approval_status = "partial"
            allocated_amount = effective_budget
        else:
            approval_status = "denied"
            allocated_amount = 0.0
        
        result = {
            "status": approval_status,
            "requested": requested_amount,
            "allocated": allocated_amount,
            "effective_budget": effective_budget,
            "base_budget": self.state.budget,
            "peer_trust_multiplier": self.get_peer_trust(peer_id).trust_multiplier,
            "purpose": purpose,
            "timestamp": time.time()
        }
        
        # Record the allocation attempt
        self._append_event({
            "kind": "allocation_request",
            "peer": peer_id,
            "result": result,
            "ts": time.time()
        })
        
        return result
    
    def record_peer_contribution(self, peer_id: str, value: float, 
                                success: bool, context: Dict[str, Any] = None) -> None:
        """
        Record a peer's contribution to update their trust metrics
        """
        cost_impact = 0.0
        value_impact = value if success else 0.0
        
        if not success:
            # Failed contributions may have cost impact
            cost_impact = abs(value) * 0.1  # Assume 10% cost for failed attempts
        
        self.update_peer_trust(
            peer_id=peer_id,
            success=success,
            value_delta=value_impact,
            cost_delta=cost_impact
        )
        
        # Also record in main economy events
        self._append_event({
            "kind": "peer_contribution",
            "peer": peer_id,
            "value": value,
            "success": success,
            "cost_impact": cost_impact,
            "context": context or {},
            "ts": time.time()
        })
        self._save()
    
    def get_trust_ranking(self) -> List[Dict[str, Any]]:
        """Get ranking of peers by trustworthiness"""
        rankings = []
        for peer_id, metrics in self.trust_metrics.items():
            rankings.append({
                "peer_id": peer_id,
                "trust_multiplier": metrics.trust_multiplier,
                "historical_alignment": metrics.historical_alignment,
                "reputation_score": metrics.reputation_score,
                "interaction_count": metrics.interaction_count,
                "net_impact": metrics.net_impact,
                "last_interaction_days": (time.time() - metrics.last_interaction) / 86400
            })
        
        # Sort by trust multiplier descending
        return sorted(rankings, key=lambda x: x["trust_multiplier"], reverse=True)
    
    def decay_inactive_peers(self, days_threshold: int = 30) -> None:
        """Apply decay to peers who haven't interacted recently"""
        cutoff_time = time.time() - (days_threshold * 86400)
        decayed_count = 0
        
        for peer_id, metrics in self.trust_metrics.items():
            if metrics.last_interaction < cutoff_time:
                # Apply time-based decay
                old_multiplier = metrics.trust_multiplier
                metrics.last_interaction = time.time()  # Reset interaction time
                new_multiplier = metrics.trust_multiplier
                
                if old_multiplier != new_multiplier:
                    decayed_count += 1
                    self._append_event({
                        "kind": "trust_decay",
                        "peer": peer_id,
                        "old_multiplier": old_multiplier,
                        "new_multiplier": new_multiplier,
                        "ts": time.time()
                    })
        
        if decayed_count > 0:
            self._save_trust_metrics()
            self._append_event({
                "kind": "decay_cycle",
                "decayed_peers": decayed_count,
                "threshold_days": days_threshold,
                "ts": time.time()
            })
            self._save()

# Global instance
_rwe_instance: Optional[ReputationWeightedEconomy] = None

def get_rwe() -> ReputationWeightedEconomy:
    """Get singleton RWE instance"""
    global _rwe_instance
    if _rwe_instance is None:
        _rwe_instance = ReputationWeightedEconomy()
    return _rwe_instance

def reset_rwe() -> None:
    """Reset RWE instance (for testing)"""
    global _rwe_instance
    _rwe_instance = None