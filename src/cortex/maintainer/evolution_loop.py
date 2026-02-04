# brain/maintainer/evolution_loop.py

from brain.maintainer.types import PainScore, SignalSummary
from brain.maintainer.mentor import ask_mentors
from brain.maintainer.memory import record_maintainer_event
from brain.core.orchestrator import get_orchestrator
from brain.core.tools.base import ToolInvocationEnvelope

def maybe_evolve(pain: PainScore, signals: SignalSummary):
    """
    The Core Decision Logic.
    Decides whether to suffer in silence or propose a mutation.
    """
    
    # 1. Do Nothing Check (Most common path)
    if pain.upgrade_pressure < 0.6:
        # Log low pain occasionally?
        # record_maintainer_event("cycle_skip", {"reason": "low_pressure", "pressure": pain.upgrade_pressure})
        return

    # 2. Consult Mentors (Expensive step, only if pain is real)
    topic = f"Pain in {pain.domains_in_pain}"
    mentors_advice = ask_mentors(topic, signals)
    
    # 3. Final Confidence Check
    # If monitors disagree or we are unsure, don't act.
    if pain.confidence < 0.5 and mentors_advice.consensus_score < 0.7:
        record_maintainer_event("cycle_abort", {"reason": "low_confidence", "topic": topic})
        return

    # 4. Propose Mutation (The Act)
    proposed_diff = f"// TODO: Generate code based on {mentors_advice.suggested_action}"
    
    orchestrator = get_orchestrator()
    envelope = ToolInvocationEnvelope(
        tool_name="evolution",
        domain="evolution",
        action="propose_patch",
        context={
            "environment": "sandbox",
            "reason": f"Pain in {pain.domains_in_pain}. Advice: {mentors_advice.advice}",
            "mentor_advice": mentors_advice.dict(),
            "diff": proposed_diff
        },
        risk_level="high",
        estimated_cost=5.0,
        requires_validation=True,
        rollback_allowed=True
    )
    
    try:
        result = orchestrator.invoke(envelope)
        record_maintainer_event("evolution_proposed", {"result": str(result.output)})
    except Exception as e:
        record_maintainer_event("evolution_failed", {"error": str(e)})
