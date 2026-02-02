from __future__ import annotations
# @cognitive - IPPOC Core Logic

import json
import os
import time
import asyncio
from dataclasses import asdict
from typing import Any, Dict, Optional

from brain.core.ledger import get_ledger
from brain.core.orchestrator import get_orchestrator
from brain.core.tools.base import ToolInvocationEnvelope
from brain.core.economy import get_economy
from brain.maintainer.observer import collect_signals
from brain.core.intents import Intent, IntentStack, IntentType
from brain.evolution.evolver import get_evolver
from brain.memory.consolidation import get_hippocampus
from brain.social.trust import get_trust_model
from brain.explain import log_decision
from brain.core.canon import violates_canon


STATE_PATH = os.getenv("AUTONOMY_STATE_PATH", "data/autonomy_state.json")
EXPLAIN_PATH = os.getenv("AUTONOMY_EXPLAIN_PATH", "data/explainability.json")


class Planner:
    """
    The Strategic Layer.
    Decides WHAT should be done based on the Hierarchy of Needs.
    """
    def plan(self, observation: Dict[str, Any], intents: IntentStack) -> Optional[Intent]:
        # 0. Social Gatekeeping (Trust Check)
        trust_model = get_trust_model()
        # Filter out intents from untrusted sources
        # We modify the stack in-place to remove bad apples
        allowed_intents = []
        for i in intents.intents:
            is_valid = trust_model.verify_intent_source(i.source)
            if is_valid:
                allowed_intents.append(i)
            else:
                score = trust_model.get_trust(i.source)
                print(f"[Planner] Social Gatekeeper REJECTED intent from {i.source} (Trust: {score})")
                log_decision(
                    action="reject",
                    reason=f"trust_below_threshold ({score})",
                    intent=i.to_dict()
                )
                continue

            # 0.1 Canon Gatekeeping (Sovereignty Check)
            # The Law: No intent can violate these rules, even from trusted sources
            if violates_canon(i):
                 print(f"[Planner] Sovereignty Gatekeeper REJECTED intent from {i.source} (Canon Violation)")
                 log_decision(
                    action="reject",
                    reason=f"canon_violation ({i.description})",
                    intent=i.to_dict()
                 )
                 continue

            allowed_intents.append(i)
        intents.intents = allowed_intents

        # 1. Survival Check (Observer Signals)
        pain_score = observation.get("pain_score", 0.0)
        
        # Rule: Pain > 0.3 triggers generic maintenance
        if pain_score > 0.3:
            # Check if we already have a maintenance intent to avoid spamming
            # Simple dedup based on type for now
            has_maintain = any(i.intent_type == IntentType.MAINTAIN for i in intents.intents)
            
            if not has_maintain:
                intents.add(Intent(
                    description=f"Investigate system pain (score: {pain_score:.2f})",
                    priority=min(pain_score + 0.2, 1.0),
                    intent_type=IntentType.MAINTAIN,
                    source="system_pain",
                    context={"pain_score": pain_score}
                ))
        
        # 2. Duty Check (External Requests)
        # TODO: Check Orchestrator/API queue for user requests
        # For now, we simulate this or rely on previous injection
        
        # 3. Growth Check (Idleness / Curiosity)
        # If no urgent intents, and budget is healthy, maybe explore?
        economy = get_economy()
        budget_healthy = economy.check_budget(0.4)
        
        if not intents.top() and budget_healthy and pain_score < 0.1:
             # Basic boredom mechanic
             intents.add(Intent(
                 description="Explore low-risk optimization",
                 priority=0.4,
                 intent_type=IntentType.EXPLORE,
                 source="boredom"
             ))

        # 4. Rest Check (Default)
        if not intents.top():
            return None # Will trigger Idle in Decider

        return intents.top()


class Decider:
    """
    The Tactical Layer.
    Decides IF the chosen intent can be executed right now.
    """
    def decide(self, observation: Dict[str, Any], intent: Optional[Intent]) -> Dict[str, Any]:
        economy = get_economy()
        pain_score = observation.get("pain_score", 0.0)
        
        # 0. Canon Backstop (Sovereignty)
        # Even if Planner failed, the Tactical Layer must refuse bad orders
        if intent and violates_canon(intent):
            return {"action": "reject", "reason": "canon_violation_backstop"}

        # 0.5 Survival override (NON-NEGOTIABLE)
        if intent and intent.intent_type == IntentType.MAINTAIN:
             # Survival instincts ignore budget (mostly)
             return {"action": "act", "intent": intent, "reason": "survival_override"}

        # 1. No Intent -> Idle
        if intent is None:
            return {"action": "idle", "reason": "no_intent"}
            
        # 2. Growth override (allowed when budget is not zero)
        if intent.intent_type == IntentType.LEARN:
            if economy.state.budget > 0:
                return {"action": "act", "intent": intent, "reason": "learning_allowed"}

        # 3. Budget Gate (Normal)
        if not economy.check_budget(intent.priority):
             return {"action": "idle", "reason": "low_budget"}

        # 4. Cooldown / Throttling
        if observation.get("recent_actions", 0) > 10 and intent.priority < 0.7:
             return {"action": "idle", "reason": "cooldown_active"}

        return {"action": "act", "intent": intent, "reason": "intent_approved"}


class Reflector:
    def evaluate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        success = result.get("success", False)
        return {
            "success": success,
            "value": 1.0 if success else -0.5,
            "notes": result.get("message") or result.get("error_code")
        }


class AutonomyController:
    def __init__(self) -> None:
        self.ledger = get_ledger()
        self.orchestrator = get_orchestrator()
        self.intent_stack = IntentStack()
        self.planner = Planner()
        self.decider = Decider()
        self.reflector = Reflector()
        self._load_state()

    def _load_state(self) -> None:
        if os.path.exists(STATE_PATH):
            try:
                with open(STATE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Rehydrate intents
                for intent_data in data.get("intents", []):
                    # Convert string enum back to Enum if needed, or rely on compatibility
                    self.intent_stack.add(Intent(**intent_data))
            except Exception:
                pass

    def _save_state(self) -> None:
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        # Convert dataclasses to dicts
        data = {"intents": [asdict(i) for i in self.intent_stack.intents]}
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _record_explain(self, explanation: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(EXPLAIN_PATH), exist_ok=True)
        with open(EXPLAIN_PATH, "w", encoding="utf-8") as f:
            json.dump(explanation, f, indent=2)

    async def observe(self) -> Dict[str, Any]:
        # Delegate observation to the Maintainer/Observer
        signal = await collect_signals()
        return signal.dict() # pydantic conversion

    async def act(self, intent: Intent) -> Dict[str, Any]:
        """
        Translates High-Level Intent -> Tool Execution
        """
        # 1. Maintain (Repair/Health Check)
        if intent.intent_type == IntentType.MAINTAIN:
            envelope = ToolInvocationEnvelope(
                tool_name="maintainer",
                domain="cognition",
                action="tick",
                context=intent.context or {},
                risk_level="low",
                estimated_cost=0.0,
                caller="autonomy",
                source=intent.source,
            )
            
        # 2. Serve (Memory/Search/etc)
        elif intent.intent_type == IntentType.SERVE:
             # Placeholder: In reality needs to look at context to pick tool
             envelope = ToolInvocationEnvelope(
                tool_name="memory",
                domain="memory",
                action="retrieve",
                context=intent.context,
                risk_level="low",
                estimated_cost=0.1,
                caller="autonomy",
                source=intent.source,
            )
            
        # 3. Explore (Graph traversal/Pattern search)
        elif intent.intent_type == IntentType.EXPLORE:
             envelope = ToolInvocationEnvelope(
                tool_name="memory",
                domain="memory",
                action="search_patterns", # hypothetical tool
                context={"limit": 1},
                risk_level="low",
                estimated_cost=0.1,
                caller="autonomy",
                source=intent.source,
            )
            
        # 4. Learn / Evolve (Self-Improvement)
        elif intent.intent_type == IntentType.LEARN:
            evolver = get_evolver()
            # Simple simulation of initiating evolution
            # In real system, this might return a Future or Job ID
            mutation = await evolver.propose_mutation(intent, goal=intent.description)
            await evolver.generate_patch(mutation.mutation_id)
            # We don't wait for full cycle in act(), just kick it off
            return {"success": True, "message": f"Evolution started: {mutation.mutation_id}", "mutation_id": mutation.mutation_id}

        # Default fallback
        else:
             return {"success": False, "message": f"Unknown intent type: {intent.intent_type}"}

        result = await self.orchestrator.invoke_async(envelope)
        return result.model_dump() if hasattr(result, "model_dump") else result.dict()

    async def learn(self, intent: Intent, evaluation: Dict[str, Any]) -> None:
        # Record skill memory using orchestrator
        # TODO: Only learn if statistically significant
        pass 
#         envelope = ToolInvocationEnvelope(
#             tool_name="memory",
#             domain="memory",
#             action="store_skill",
#             context={"skill": str(intent.intent_type), "success": evaluation.get("success", False)},
#             risk_level="low",
#             estimated_cost=0.0,
#             caller="autonomy",
#             source="autonomy",
#         )
#         await self.orchestrator.invoke_async(envelope)

    async def run_cycle(self) -> Dict[str, Any]:
        observation = await self.observe()
        
        self.intent_stack.decay()
        intent = self.planner.plan(observation, self.intent_stack)
        
        decision = self.decider.decide(observation, intent)

        explanation = {
            "time": time.time(),
            # Convert decision's intent to dict if present
            "decision": {k: (asdict(v) if isinstance(v, Intent) else v) for k, v in decision.items()},
            "observation": observation,
        }

        # --- TERMINAL GATES ---
        if decision["action"] == "reject":
            # Sovereignty Violation Refusal
            print(f"[Autonomy] REFUSING intent from {intent.source}: {decision['reason']}")
            # Ensure we log the refusal
            self._record_explain({**explanation, "result": "refused"})
            self._save_state()
            # Remove bad intent from stack to prevent looping
            if intent and intent in self.intent_stack.intents:
                 self.intent_stack.intents.remove(intent)
            return {"status": "rejected", "reason": decision["reason"]}

        if decision["action"] == "idle":
            self._record_explain({**explanation, "result": "idle"})
            self._save_state()
            
            # TRIGGER SLEEP / CONSOLIDATION
            # If idle, take the opportunity to consolidate memories
            hippocampus = get_hippocampus()
            stats = await hippocampus.consolidate()
            if stats["pruned"] > 0:
                # Log pruning somewhere if needed
                pass
            
            return {"status": "idle", "reason": decision["reason"], "memory_stats": stats}

        # Execute
        try:
            result = await self.act(decision["intent"])
        except Exception as e:
            # Log the crash so we know what we tried to do
            self._record_explain({**explanation, "result": {"error": str(e), "status": "crashed"}})
            # Re-raise so the caller (orchestrator/test) knows
            raise e
        
        # Remove intent if satisfied (simplistic completion logic)
        if hasattr(decision["intent"], "intent_type"):
            # If successful, assume intent is fulfilled for now
             if result.get("success", True): # Default to true if not specified?
                 # For stack, we might want to pop specific ID. 
                 # For now, simplistic clear of the type or just let it decay/remove
                 # Better: remove specific intent
                 if decision["intent"] in self.intent_stack.intents:
                     self.intent_stack.intents.remove(decision["intent"])

        evaluation = self.reflector.evaluate(result)
        await self.learn(decision["intent"], evaluation)

        self._record_explain({**explanation, "result": result, "evaluation": evaluation})
        self._save_state()
        return {"status": "acted", "result": result, "evaluation": evaluation}


async def run_autonomy_loop(interval_seconds: int = 60) -> None:
    controller = AutonomyController()
    while True:
        try:
            await controller.run_cycle()
        except Exception:
            # Log error?
            pass
        await asyncio.sleep(interval_seconds)
