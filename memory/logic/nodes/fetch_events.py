from memory.logic.state import MemoryState

def fetch_events(state: MemoryState) -> dict:
    """
    Episodic Intake Node.
    Currently a pass-through as events are injected into the initial state.
    Future: Could poll an event bus or queue.
    """
    return {} # No state update needed, just passing through
