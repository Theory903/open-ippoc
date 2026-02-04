# brain/memory/consolidation.py
# @cognitive - IPPOC Hippocampus (Memory Consolidation)

from __future__ import annotations

import time
import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from cortex.core.ledger import get_ledger
from cortex.core.orchestrator import get_orchestrator


@dataclass
class MemoryEntry:
    memory_id: str
    content: str
    created_at: float
    last_accessed: float
    importance: float  # 0.0 to 1.0
    access_count: int = 1
    memory_type: str = "episodic" # episodic, semantic, skill


class Hippocampus:
    """
    Manages the lifecycle of memories:
    - Decay: Importance drops over time.
    - Consolidation: High importance memories are summarized/reinforced.
    - Pruning: Low importance memories are forgotten.
    """
    def __init__(self) -> None:
        self.orchestrator = get_orchestrator()
        # In a real system, this connects to the Vector DB or Memory Store
        # For now, we mock an in-memory store for the logic
        self.memories: Dict[str, MemoryEntry] = {}

    async def add_memory(self, content: str, importance: float = 0.5, mem_type: str = "episodic") -> MemoryEntry:
        import uuid
        mem_id = str(uuid.uuid4())
        entry = MemoryEntry(
            memory_id=mem_id,
            content=content,
            created_at=time.time(),
            last_accessed=time.time(),
            importance=importance,
            memory_type=mem_type
        )
        self.memories[mem_id] = entry
        return entry

    async def access_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        entry = self.memories.get(memory_id)
        if entry:
            entry.last_accessed = time.time()
            entry.access_count += 1
            # Boost importance on access (simple Hebbian reinforcement)
            entry.importance = min(entry.importance + 0.1, 1.0)
        return entry

    async def consolidate(self) -> Dict[str, int]:
        """
        Runs the Sleep Cycle:
        1. Apply Decay to all memories.
        2. Prune dead memories.
        3. (Future) Summarize high-value memories.
        """
        now = time.time()
        kept = 0
        pruned = 0
        
        # Decay Parameters
        # Half-life of importance ~ 24 hours (86400 seconds)
        # formula: N(t) = N0 * (0.5)^(t / half_life)
        half_life = 86400.0 
        
        to_remove = []
        
        for mem_id, entry in self.memories.items():
            dt = now - entry.last_accessed
            
            # Decay Factor
            decay = math.pow(0.5, dt / half_life)
            
            # Apply decay
            entry.importance *= decay
            
            # Pruning Threshold (0.1)
            if entry.importance < 0.1:
                to_remove.append(mem_id)
            else:
                kept += 1
                
        for mem_id in to_remove:
            del self.memories[mem_id]
            pruned += 1
            
        return {"kept": kept, "pruned": pruned}

_hippocampus_instance: Hippocampus | None = None

def get_hippocampus() -> Hippocampus:
    global _hippocampus_instance
    if _hippocampus_instance is None:
        _hippocampus_instance = Hippocampus()
    return _hippocampus_instance
