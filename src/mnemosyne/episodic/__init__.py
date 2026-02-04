# __init__.py
"""
MODULE: memory.episodic

ROLE:
    Short-term episodic log.
    Stores "What happened" (Logs, Chat History, Events).
    Pruned regularly or compressed into Semantic memory.

OWNERSHIP:
    Memory subsystem.

PUBLIC API:
    - log_event(event)
    - get_recent_history(n) -> List[Event]
"""
