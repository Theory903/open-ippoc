# brain/core/intents.py
# @cognitive - IPPOC Intent Definitions

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class IntentType(str, Enum):
    MAINTAIN = "maintain"   # Survival: Fix pain (errors, latency)
    SERVE = "serve"         # Duty: Fulfill user request
    LEARN = "learn"         # Growth: Curiosity, experimentation
    EXPLORE = "explore"     # Growth: Low-risk discovery
    IDLE = "idle"           # Rest: Save budget / cooldown


@dataclass
class Intent:
    description: str
    priority: float  # 0.0 to 1.0
    intent_type: IntentType
    
    intent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    source: str = "system"  # 'system', 'user', 'mentor'
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Dynamic properties
    decay_rate: float = 0.01  # Priority loss per second (if in stack)

    def decay(self) -> None:
        """Applies time-based decay to priority."""
        elapsed = max(time.time() - self.created_at, 0.0)
        # Use a simpler linear decay for now
        # Maybe exponential later if needed
        self.priority = max(self.priority - (self.decay_rate * 0.01 * elapsed), 0.0) 
        # adjusted decay factor to be less aggressive than raw seconds

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)


class IntentStack:
    def __init__(self) -> None:
        self.intents: List[Intent] = []

    def add(self, intent: Intent) -> None:
        # Check for duplicates? For now, just append.
        self.intents.append(intent)

    def decay(self) -> None:
        """Decay all intents and remove dead ones."""
        for intent in self.intents:
            intent.decay()
        # Filter out intents that have decayed to near zero
        self.intents = [i for i in self.intents if i.priority > 0.01]

    def top(self) -> Optional[Intent]:
        """Returns the highest priority intent."""
        if not self.intents:
            return None
        # Sort by priority desc
        return sorted(self.intents, key=lambda i: i.priority, reverse=True)[0]
    
    def clear_type(self, intent_type: IntentType) -> None:
        """Remove all intents of a specific type (e.g. after fulfilling one)"""
        self.intents = [i for i in self.intents if i.intent_type != intent_type]
