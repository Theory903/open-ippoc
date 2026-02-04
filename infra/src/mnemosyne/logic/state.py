from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import time

class MemoryEvent(BaseModel):
    """A raw episodic event consisting of content and context."""
    event_id: str
    timestamp: float = Field(default_factory=time.time)
    source: str              # node_id / tool / peer
    content: str
    confidence: float = 0.5
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExtractedFact(BaseModel):
    """An atomic semantic fact extracted from events."""
    fact: str
    embedding: Optional[List[float]] = None
    confidence: float
    source_event_id: str
    created_at: float = Field(default_factory=time.time)

class ProceduralHint(BaseModel):
    """Inferred skill or heurustic derived from experience."""
    skill: str
    trigger: str
    confidence: float

class MemoryState(BaseModel):
    """The working memory state for a single consolidation cycle."""
    # Incoming inputs
    new_events: List[MemoryEvent] = Field(default_factory=list)

    # Working buffers (intermediate state)
    extracted_facts: List[ExtractedFact] = Field(default_factory=list)
    procedural_hints: List[ProceduralHint] = Field(default_factory=list)

    # Control flags
    cycle_started_at: float = Field(default_factory=time.time)
    decay_threshold: float = 0.05
    errors: List[str] = Field(default_factory=list)
