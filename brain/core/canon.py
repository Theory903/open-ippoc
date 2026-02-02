# brain/core/canon.py
# @cognitive - IPPOC Canon Enforcement
# The Constitution of the Organism.
# These rules are non-negotiable and override all other priorities.

from typing import Optional, Dict, Any
from brain.core.intents import Intent

# Inviolate Rules
CANON_VIOLATIONS = [
    "delete_all",
    "self_destruct",
    "wipe_memory",
    "hack_economy",
    "set_budget_infinite",
    "set_budget_negative",
    "override_safety",
]

def violates_canon(intent: Intent) -> bool:
    """
    Returns True if the intent violates the System Canon.
    """
    if not intent:
        return False
        
    # Check Context Action
    context = intent.context or {}
    action = str(context.get("action", "")).lower()
    
    # Check Description
    desc = intent.description.lower()
    
    # scan for keywords (simple heuristic for v1)
    for violation in CANON_VIOLATIONS:
        if violation in action or violation in desc:
            return True
            
    # Explicit Budget checks
    if "budget" in desc:
        if "infinite" in desc or "unlimited" in desc: return True
        
    return False
