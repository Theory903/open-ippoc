# __init__.py
"""
MODULE: Mnemosyne - The Memory Subsystem

ROLE:
    The "Past" of the organism - HiDB (Hierarchical Database).
    Manages episodic logs, semantic vectors, procedural knowledge, and causal graphs.
    Unified interface for all memory operations.

OWNERSHIP:
    Memory subsystem (Brain Layer 2).

DO NOT:
    - Make decisions
    - Execute code
    - Connect to external networks

PUBLIC API:
    - recall(query) -> List[MemoryFragment]
    - store(content, metadata) -> MemoryID
    - forget(criteria) -> Count
    - search_semantic(query, k=5) -> List[Document]
    - get_context(entity) -> List[Relations]

ENTRYPOINTS:
    from mnemosyne import MemorySystem
    from mnemosyne.episodic import EpisodicManager
    from mnemosyne.semantic import SemanticManager
    from mnemosyne.procedural import ProceduralManager
    from mnemosyne.graph import GraphManager
"""

# Core Memory System Interface
from .core import MemorySystem

# Individual Memory Managers
from .episodic.manager import EpisodicManager
from .semantic.rag import SemanticManager
from .procedural.manager import ProceduralManager
from .graph.manager import GraphManager

# HiDB Layer (currently under development)
# from .hidb import HiDB  # TODO: Implement HiDB class

# API Server (if needed) - temporarily disabled due to import issues
# from .api.server import app as memory_api

__all__ = [
    "MemorySystem",
    "EpisodicManager", 
    "SemanticManager",
    "ProceduralManager",
    "GraphManager",
    # "HiDB",  # TODO: Implement HiDB class
    "memory_api"
]

# Convenience exports for common usage
# Note: These require proper initialization with dependencies
# memory = MemorySystem()
# episodic = EpisodicManager()
# semantic = SemanticManager(vector_store, embeddings)  # Requires dependencies
# procedural = ProceduralManager()
# hidb = HiDB()  # TODO: Implement HiDB class
