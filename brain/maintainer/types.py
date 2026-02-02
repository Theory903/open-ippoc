# brain/maintainer/types.py

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class SignalSummary(BaseModel):
    """
    aggregated health signals from the system.
    """
    errors_last_hour: int = 0
    avg_cost: float = 0.0
    success_rate: float = 1.0
    mutation_rejects: int = 0
    latency_trend: str = "stable" # "up", "down", "stable"
    raw_metrics: Dict[str, Any] = Field(default_factory=dict)

class PainScore(BaseModel):
    """
    The 'feeling' of the system.
    """
    upgrade_pressure: float = Field(..., ge=0.0, le=1.0, description="0.0 = content, 1.0 = desperate for change")
    domains_in_pain: List[str] = Field(default_factory=list, description="Which domains are causing pain (e.g. 'coding', 'memory')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="How sure are we that pain is real?")

class MentorAdvice(BaseModel):
    """
    Guidance from the Swarm/Mentors.
    """
    topic: str
    advice: str
    suggested_action: Optional[str] = None
    consensus_score: float = 0.0
