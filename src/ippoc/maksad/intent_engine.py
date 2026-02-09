import asyncio
import time
import uuid
import os
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from .cognitive_bus import emit_thought

logger = logging.getLogger(__name__)

class IntentStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    DECAYED = "decayed"

class Intent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    urgency: float = 0.5  # 0.0 to 1.0
    confidence: float = 1.0
    created_at: float = Field(default_factory=time.time)
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: IntentStatus = IntentStatus.PENDING
    mission_id: Optional[str] = None

class Mission(BaseModel):
    id: str = Field(default_factory=lambda: f"mission_{int(time.time())}")
    title: str
    description: str
    intent_ids: List[str] = Field(default_factory=list)
    status: str = "active"

class IntentEngine:
    """
    Chronos - The Unified Autonomy Engine of IPPOC.
    Enforces the single loop of Intent, Reflection, Curiosity, and Decay.
    """
    def __init__(self):
        self.intents: Dict[str, Intent] = {}
        self.missions: Dict[str, Mission] = {}
        self._lock = asyncio.Lock()
        self.last_reflection_time = 0

    async def add_intent(self, goal: str, urgency: float = 0.5, ttl: Optional[float] = 3600, mission_id: Optional[str] = None) -> str:
        async with self._lock:
            expires_at = time.time() + ttl if ttl else None
            intent = Intent(goal=goal, urgency=urgency, expires_at=expires_at, mission_id=mission_id)
            self.intents[intent.id] = intent
            
            # Emit to Neural Interface
            await emit_thought("intent", f"Goal Acquired: {goal}", {
                "urgency": urgency, 
                "iid": intent.id, 
                "mid": mission_id
            })
            
            return intent.id

    async def create_mission(self, title: str, description: str, goals: List[str]) -> str:
        """Coordinated strategic mission involving multiple sub-intents."""
        mission = Mission(title=title, description=description)
        for goal in goals:
            iid = await self.add_intent(goal, urgency=0.7, mission_id=mission.id)
            mission.intent_ids.append(iid)
        
        async with self._lock:
            self.missions[mission.id] = mission
        
        await emit_thought("info", f"Strategic Mission Formed: {title}", {"mid": mission.id})
        return mission.id

    async def get_active_intents(self) -> List[Intent]:
        async with self._lock:
            now = time.time()
            active = []
            for iid, intent in list(self.intents.items()):
                # DECAY LOOP: Enforce memory hygiene
                if intent.expires_at and now > intent.expires_at:
                    if intent.status not in [IntentStatus.COMPLETED, IntentStatus.DECAYED]:
                        intent.status = IntentStatus.DECAYED
                        await emit_thought("info", f"Intent Decayed: {intent.goal}", {"iid": iid})
                    continue
                
                if intent.status in [IntentStatus.PENDING, IntentStatus.ACTIVE]:
                    active.append(intent)
            
            # Sort by Urgency (Priority-based scheduling)
            return sorted(active, key=lambda x: x.urgency, reverse=True)

    async def run_reflection(self):
        """Metabolic Reflection over memory and state."""
        from .reflection_engine import get_reflection_engine
        refl = get_reflection_engine()
        await refl.run_reflection_cycle()
        self.last_reflection_time = time.time()

    async def run_tick(self):
        """Single Autonomy Cycle."""
        active = await self.get_active_intents()
        
        # 1. Processing
        if active:
            top = active[0]
            # Emit "current focus" state if needed
        
        # 2. Periodic Reflection & Curiosity (Every 5 mins)
        if time.time() - self.last_reflection_time > 300:
            await self.run_reflection()

    async def main_loop(self, interval: int = 60):
        print(f"🕒 [Chronos] Unified Autonomy Loop started (tick: {interval}s)")
        while True:
            try:
                await self.run_tick()
            except Exception as e:
                logger.error(f"[Chronos] Loop failure: {e}")
            await asyncio.sleep(interval)

_engine_instance: Optional[IntentEngine] = None

def get_intent_engine() -> IntentEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = IntentEngine()
    return _engine_instance
