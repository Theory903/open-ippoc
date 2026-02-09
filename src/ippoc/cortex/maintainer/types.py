# brain/maintainer/types.py
# @cognitive - IPPOC Maintainer Types

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class Trend(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"


class PressureSource(str, Enum):
    COST = "cost"
    ERRORS = "errors"
    LATENCY = "latency"
    MEMORY_PRESSURE = "memory_pressure"


class SignalSummary(BaseModel):
    """
    The calculated 'health state' of the organism.
    """
    pain_score: float = Field(..., ge=0.0, le=1.0, description="0.0 = Zen, 1.0 = Agony")
    pressure_sources: List[PressureSource] = Field(default_factory=list)
    trend: Trend = Field(default=Trend.STABLE)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Reliability of this signal")
    
    # Raw metrics for debugging/logging, not for decision making if possible
    raw_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # Deprecated fields kept temporarily if needed but should be subsumed by raw_metrics or pain_score
    errors_last_hour: int = 0
    avg_cost: float = 0.0
    success_rate: float = 1.0


class MentorAdvice(BaseModel):
    """
    Guidance from the Swarm/Mentors.
    """
    topic: str
    advice: str
    suggested_action: Optional[str] = None
    consensus_score: float = 0.0


class PainScore(BaseModel):
    """
    Structured pain/pressure report.
    """
    upgrade_pressure: float = Field(..., ge=0.0, le=1.0)
    domains_in_pain: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
