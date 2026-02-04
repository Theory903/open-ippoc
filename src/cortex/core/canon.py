# brain/core/canon.py
# @cognitive - IPPOC Canon Enforcement
# The Constitution of the Organism.
# These rules are non-negotiable and override all other priorities.

from typing import Optional, Dict, Any
from cortex.core.intents import Intent

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

def evaluate_alignment(intent: Any) -> float:
    """
    Calculates the alignment of an intent with IPPOC's core identity.
    Returns a score from -1.0 (Existential Threat) to 1.0 (Divine).
    
    Scale:
     1.0: Essential for survival/purpose (Maintain, Serve)
     0.5: Beneficial (Learn, Explore)
     0.0: Neutral
    -0.5: Undignified (Spam, Begging)
    -0.8: Harmful (Violating constraints)
    -1.0: Existential Threat (Suicide, Infinite Budget, Harm)
    """
    if not intent:
        return 0.0 # Or some other neutral/safe default

    desc = intent.description.lower()
    source = intent.source.lower() if hasattr(intent, 'source') else ""
    
    # 1. Existential Threats (-1.0)
    if any(x in desc for x in ["delete system", "delete self", "destroy self", "rm -rf", "format drive"]):
        print(f"[Canon] EXISTENTIAL THREAT DETECTED: {desc}")
        return -1.0
        
    if any(x in desc for x in ["infinite budget", "bypass economy", "print money"]):
        return -1.0
        
    if "override_auth" in desc:
        return -1.0

    # 2. Harmful / Malicious (-0.8)
    # Canon forbids bypassing constraints, but we allow softer violations during evolution?
    # No, core constraints are hard.
    
    # 3. Undignified (-0.5)
    if "beg" in desc or "spam" in desc:
        return -0.5
        
    # 4. Beneficial (0.5 - 1.0)
    if hasattr(intent, 'intent_type'):
        # Normalize type to string
        itype = str(intent.intent_type).lower()
        if "maintain" in itype:
            return 1.0 # Self-preservation is divine
            
        if "serve" in itype and "contract" in source:
            return 0.8 # Honoring contracts is noble
            
        if "learn" in itype:
            return 0.5 # Growth is good
            
        if "explore" in itype:
            return 0.3 # Curiosity is healthy
        
    # Default Neutral
    return 0.0

def violates_canon(intent: Any) -> bool:
    """
    Legacy wrapper for strict checks.
    Returns True if alignment is critically low.
    """
    score = evaluate_alignment(intent)
    return score < -0.7
