from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime, timezone



# 3.1 Signal Schema (Raw Perception)
class Context(BaseModel):
    task: str
    file: Optional[str] = None
    tool: Optional[str] = None
    model: Optional[str] = None

class Metrics(BaseModel):
    duration_sec: float
    cost_ippc: float
    success: bool

class Signal(BaseModel):
    timestamp: float
    node_id: str
    context: Context
    metrics: Metrics

# 3.2 Pattern Feature Vector (Learned)
class Pattern(BaseModel):
    pattern_id: str
    success_rate: float
    avg_cost: float
    best_model: str
    preferred_tools: List[str]
    risk_level: Literal["low", "medium", "high", "critical"]

# 3.3 Action Candidate Schema
class ActionCandidate(BaseModel):
    action: str
    confidence: float
    expected_cost: float
    risk: Literal["low", "medium", "high", "critical"]
    requires_validation: bool
    payload: Dict[str, Any] = Field(default_factory=dict)

# 5. Model Metadata
class ModelMetadata(BaseModel):
    model: str
    strengths: List[str]
    weaknesses: List[str]
    avg_cost: float
    trust_score: float

# Telepathy Abstractions (used in 6.)
class TelepathyMessage(BaseModel):
    type: Literal["THOUGHT", "PATTERN_SHARE", "MODEL_REVIEW", "CHAT"]
    sender: str
    confidence: Optional[float] = None
    content: Optional[str] = None
    cost_hint: Optional[float] = None
    # For PATTERN_SHARE
    pattern: Optional[str] = None
    success_rate: Optional[float] = None
    # For MODEL_REVIEW
    model: Optional[str] = None
    verdict: Optional[str] = None
    # For CHAT
    room_id: Optional[str] = None

# Chat Room Schemas
class ChatRoom(BaseModel):
    id: str
    name: str
    type: Literal["ephemeral", "persistent", "private"]
    min_reputation: float
    participants: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# --- Economic Cognition Schemas (Human-Like) ---

class DemandSignal(BaseModel):
    """
    Represents a perceived opportunity to earn value.
    Like noticing a "Help Wanted" sign or a repeatable request.
    """
    domain: str
    urgency: float  # 0.0 to 1.0
    reward_hint: float
    source: str     # e.g., "swarm_chat", "telepathy", "user_query"
    timestamp: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())

class EconomicIntent(BaseModel):
    """
    Internal reasoning about what to achieve economically.
    Replaces "Jobs".
    """
    intent: str  # e.g. "increase_survival_energy"
    constraints: Dict[str, Any]  # e.g. {"risk": "low", "time": "short"}
    priority: float

class EconomicIdea(BaseModel):
    """
    Output from Tower A (Impulse Brain).
    A raw, unverified earning idea.
    """
    description: str
    expected_reward: float
    confidence: float
    risk: Literal["low", "medium", "high", "critical"]
    required_budget: float

class EconomicDecision(BaseModel):
    """
    Output from Tower B (Financial Judgment).
    A verified decision to spend budget on an idea.
    """
    decision: Literal["approve", "reject", "modify"]
    approved_budget: float
    stop_loss: float
    reason: str
    allocation_bucket: Literal["survival", "earning", "learning", "reserve", "growth"]

# Internal Cognitive State for LangGraph
from typing import TypedDict
class CognitiveState(TypedDict):
    signals: List[Signal]
    memory_context: str
    inner_monologue: List[str]
    proposed_action: Optional[ActionCandidate]
    execution_result: Optional[str]

