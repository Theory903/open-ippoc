# brain/market/contracts.py
# @cognitive - Market Interface Primitives

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import time
import uuid

@dataclass
class ExternalWorkUnit:
    """
    A unit of work proposed by the external market.
    """
    description: str
    reward: float  # Payment offered
    estimated_cost: float
    risk_level: float # 0.0 to 1.0 (0.0 = Safe, 1.0 = Danger)
    
    contract_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = "market"
    expires_at: float = field(default_factory=lambda: time.time() + 60.0)
    
    # Context for the job (e.g. strict payload)
    payload: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MarketDecision:
    """
    The result of evaluating a work unit.
    """
    decision: str # "accept" or "reject"
    reason: str
    will_score: float
    unit_id: str
