# brain/gateway/timeline.py
# @cognitive - Decision Timeline API

import json
import os
from typing import List, Dict, Any

EXPLAIN_PATH = os.getenv("AUTONOMY_EXPLAIN_PATH", "data/explainability.json")

def get_decision_history(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Returns the most recent decisions from the explainability log.
    Reversed (newest first).
    """
    if not os.path.exists(EXPLAIN_PATH):
        return []
    
    try:
        with open(EXPLAIN_PATH, "r", encoding="utf-8") as f:
            content = json.load(f)
            
        if not isinstance(content, list):
            content = [content] if content else []
            
        # Sort by time desc (if not already appended in order)
        # Usually appended in order, so reverse
        content.reverse()
        
        return content[:limit]
    except Exception:
        return []

def get_last_decision() -> Dict[str, Any]:
    history = get_decision_history(limit=1)
    return history[0] if history else {}
