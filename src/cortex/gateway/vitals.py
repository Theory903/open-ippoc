# brain/gateway/vitals.py
# @cognitive - Operator Vital Signs

from typing import Dict, Any
from cortex.core.economy import get_economy
from cortex.core.autonomy import AutonomyController


async def get_vital_signs() -> Dict[str, Any]:
    """
    Returns the current health/state of the IPPOC organism.
    """
    economy = get_economy()
    controller = AutonomyController() # Singleton
    
    # 1. Autonomy State (Mind)
    intent_stack = controller.intent_stack.intents
    current_intent = intent_stack[0] if intent_stack else None
    
    # 2. Signals (Pain)
    # We use the internal observer or collect fresh signals
    # Since collect_signals is async, we can await it
    from cortex.maintainer.observer import collect_signals
    signals = await collect_signals()
    
    # 3. Last Refusal (Sovereignty)
    # We check the explainability log for the last "reject" decision
    from cortex.gateway.timeline import get_decision_history
    history = get_decision_history(limit=50) # fetch recent history
    last_refusal = next((h for h in history if h.get("decision", {}).get("action") == "reject"), None)

    return {
        "heartbeat": {
            "budget": economy.state.budget,
            "reserve": economy.state.reserve,
            "status": "thriving" if economy.state.budget > 10 else "surviving",
            "trend": signals.trend.value if signals else "stable"
        },
        "mind": {
            "current_intent": current_intent.to_dict() if current_intent else None,
            "stack_depth": len(intent_stack),
            "state": "active", # Placeholder for real fsm state
            "focus": current_intent.intent_type if current_intent else "idle"
        },
        "senses": {
            "pain_score": signals.pain_score if signals else 0.0,
            "pressure_sources": [p.value for p in signals.pressure_sources] if signals else [],
            "modules_active": ["observer", "memory", "body"]
        },
        "sovereignty": {
            "last_refusal": last_refusal
        },
        "economy": {
            "total_value": economy.state.total_value,
            "total_spent": economy.state.total_spent,
            "roi": economy.state.total_value / economy.state.total_spent if economy.state.total_spent > 0 else 0.0
        }
    }
