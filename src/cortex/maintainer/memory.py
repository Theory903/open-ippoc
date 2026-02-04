# brain/maintainer/memory.py

from typing import Dict, Any
from brain.core.orchestrator import get_orchestrator
from brain.core.tools.base import ToolInvocationEnvelope

def record_maintainer_event(event_type: str, details: Dict[str, Any]):
    """
    Persists a Maintainer event to Long-Term Memory.
    Prevents amnesia about past failures/upgrades.
    """
    orchestrator = get_orchestrator()
    
    envelope = ToolInvocationEnvelope(
        tool_name="memory",
        domain="memory", 
        action="store_episodic",
        context={
            "content": f"[MAINTAINER] {event_type}: {str(details)}",
            "source": "ippoc.brain.maintainer",
            "metadata": {"type": "system_health_log", "event": event_type}
        },
        risk_level="low",
        estimated_cost=0.1
    )
    
    try:
        orchestrator.invoke(envelope)
    except Exception as e:
        print(f"[MAINTAINER] Memory write failed: {e}")
