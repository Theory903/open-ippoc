# brain/gateway/openclaw_guard.py
# @cognitive - OpenClaw Safety Gate

from brain.core.canon import violates_canon
from brain.core.intents import Intent

def guard_openclaw_request(payload: dict) -> None:
    """
    Fast reject before IPPOC even reasons.
    """
    if not isinstance(payload, dict):
        raise ValueError("Invalid OpenClaw payload")

    context = payload.get("context", {})
    description = payload.get("description", "")
    
    # We construct a dummy intent to check against Canon
    # Since canon checks description and context actions
    dummy_intent = Intent(
        description=description,
        context=context,
        intent_type="SERVE", # dummy
        source="guard",
        priority=0.0 # required field
    )

    # Canon-level kill switch
    if violates_canon(dummy_intent):
        raise PermissionError(f"Canon violation (OpenClaw request blocked): {description}")

    # Rate-limit / spam protection hooks can live here


