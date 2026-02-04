# __init__.py
"""
MODULE: memory

ROLE:
    The "Past" of the organism.
    Passive storage for episodic logs, semantic vectors, and procedural knowledge.
    The Cognitive Substrate (HiDB).

OWNERSHIP:
    Memory subsystem.

DO NOT:
    - Make decisions
    - execute code
    - Connect to network

PUBLIC API:
    - recall(query_vector) -> List[Memory]
    - store(Memory) -> ID
    - forget(criteria) -> Count

ENTRYPOINTS:
    memory.hidb
    memory.episodic
    memory.semantic
"""
