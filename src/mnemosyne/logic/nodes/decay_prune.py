from mnemosyne.logic.state import MemoryState

def decay_prune(state: MemoryState) -> dict:
    """
    Filters out facts and hints that fall below the decay threshold.
    Simulates 'forgetting' of weak memories.
    """
    
    kept_facts = [
        f for f in state.extracted_facts
        if f.confidence >= state.decay_threshold
    ]
    
    kept_hints = [
        p for p in state.procedural_hints
        if p.confidence >= state.decay_threshold
    ]
    
    # We return the filtered lists to update the state
    return {
        "extracted_facts": kept_facts,
        "procedural_hints": kept_hints
    }
