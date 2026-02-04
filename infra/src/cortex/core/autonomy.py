from __future__ import annotations
# @cognitive - IPPOC Core Logic

import json
import os
import time
import asyncio
from dataclasses import asdict
from typing import Any, Dict, Optional

from cortex.core.ledger import get_ledger
from cortex.core.orchestrator import get_orchestrator
from cortex.core.tools.base import ToolInvocationEnvelope
from cortex.core.economy import get_economy
from cortex.maintainer.observer import collect_signals
from cortex.core.intents import Intent, IntentStack, IntentType
from cortex.evolution.evolver import get_evolver
from cortex.memory.consolidation import get_hippocampus
from cortex.social.trust import get_trust_model
from cortex.explain import log_decision
from cortex.core.canon import violates_canon


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

        # 0.5 ROI Estimation (The Accountant)
        # We annotate intents with expected ROI to help prioritization
        economy = get_economy()
        for i in intents.intents:
            # Heuristic map
            likely_tool = "unknown"
            if i.intent_type == IntentType.MAINTAIN: likely_tool = "maintainer"
            elif i.intent_type == IntentType.LEARN: likely_tool = "evolver"
            elif i.intent_type == IntentType.SERVE: likely_tool = "body" # default
            elif i.intent_type == IntentType.EXPLORE: likely_tool = "observer"
            
            # Context override
            if i.context and "plugin" in i.context:
                 # plugins map to tools via map, but for stats we use the tool name
                 pass 

            stats = economy.get_tool_stats(likely_tool) if likely_tool != "unknown" else None
            # Default ROI anticipation
            roi = stats.roi if stats and stats.total_spent > 1.0 else 1.5 # Assume good if new
            
            # Store in context for Decider
            if i.context is None: i.context = {}
            i.context["expected_roi"] = roi

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
        # Always allow exploration - economy focuses on earning value
        economy = get_economy()
        
        if not intents.top() and pain_score < 0.1:
             # Basic boredom mechanic - always explore when idle
             intents.add(Intent(
                 description="Explore optimization opportunities",
                 priority=0.4,
                 intent_type=IntentType.EXPLORE,
                 source="curiosity"
             ))

        # 4. Rest Check (Default)
        if not intents.top():
            return None # Will trigger Idle in Decider

        return intents.top()


class Decider:
    """
    The Consequence Engine.
    Simulates outcomes and chooses the path of highest dignity (Score).
    """
    def decide(self, observation: Dict[str, Any], intent: Optional[Intent]) -> Dict[str, Any]:
        if intent is None:
             return {"action": "idle", "reason": "no_intent"}

        economy = get_economy()
        pain_score = observation.get("pain_score", 0.0)
        
        # 1. Simulation: Predict Consequences
        from cortex.core.canon import evaluate_alignment
        
        alignment = evaluate_alignment(intent)
        expected_roi = intent.context.get("expected_roi", 1.5)
        # Cost check (Budget drain) 
        # Note: We don't have exact cost here, but can guess from stats or tool name
        # Assume generic cost for simulation
        expected_cost = 0.5 
        
        # 2. Physiology Weights (Driven by Pain)
        # If Pain is high, Survival (Safety) and Value (Food) matter more
        w_p = 1.0 + (pain_score * 5.0) # Pain multiplier
        w_v = 1.0 * w_p # Value weight
        w_s = 2.0 * w_p # Survival (Alignment) weight
        w_c = 1.0 # Cost weight
        
        # 3. The Will Function (Score Calculation)
        # Score = (ROI * w_v) + (Alignment * w_s) - (Cost * w_c) + SocialSignal
        
        social_signal = 0.0
        # If intent has advice attached (e.g. from CONSULT result)
        if intent.context and "advice" in intent.context:
            from cortex.social.reputation import get_reputation_engine
            advice = intent.context["advice"] # {node_id, action, confidence}
            node_id = advice.get("node_id")
            conf = float(advice.get("confidence", 0.0))
            
            # Weighted Influence
            weight = get_reputation_engine().weigh_advice(node_id, conf)
            
            # Direction
            if advice.get("action") == "recommend":
                social_signal = 2.0 * weight # Strong boost
            elif advice.get("action") == "warn":
                social_signal = -2.0 * weight # Strong penalty
        
        # Special logic: If alignment is Existential Threat (-1.0), it overrides everything
        if alignment < -0.7:
             return {"action": "reject", "reason": f"undignified_act ({alignment})"}

        score = (expected_roi * w_v) + (alignment * w_s) - (expected_cost * w_c) + social_signal
        
        # 4. The Choice
        # If score is positive, we act. If negative, we idle (unless survival override).
        
        if score > 0:
             # Final Budget Check (Soft)
             # If budget is < 0 (Debt), we only act if alignment is High (MAINTAIN) or ROI is High
             if economy.state.budget < 0.0:
                 # In debt, we only allow Survival (Alignment >= 0.8) or High Profit (ROI > 3.0)
                 if alignment < 0.8 and expected_roi < 3.0:
                     return {"action": "idle", "reason": "debt_conservation"}
                     
             return {"action": "act", "intent": intent, "reason": f"will_approved (score: {score:.2f})"}
             
        # Fallback: Negative score implies action is not worth the energy
        # BUT: If it's MAINTAIN, alignment is 1.0. 
        # (1.5 * 1) + (1.0 * 2) - (0.5 * 1) = 1.5 + 2 - 0.5 = 3.0. -> Should pass.
        # Spam: ROI 0.1, Alignment -0.5.
        # (0.1 * 1) + (-0.5 * 2) - (0.5 * 1) = 0.1 - 1.0 - 0.5 = -1.4. -> Reject.
        
        return {"action": "idle", "reason": f"low_will_score ({score:.2f})"}

        # 0.5 Survival override (NON-NEGOTIABLE)
        if intent and intent.intent_type == IntentType.MAINTAIN:
             # Survival instincts ignore budget (mostly)
             return {"action": "act", "intent": intent, "reason": "survival_override"}

        # 1. No Intent -> Idle
        if intent is None:
            return {"action": "idle", "reason": "no_intent"}

        # 1.5 Performance Optimization (ROI Guidance)
        # ROI analysis for tool selection, NOT blocking
        expected_roi = intent.context.get("expected_roi", 1.5)
        if expected_roi < 1.0:
            # Log for performance analysis but don't block
            print(f"[Autonomy] Low ROI intent detected: {expected_roi:.2f} (continuing anyway)")

        # 2. Growth allowance (always allowed)
        if intent.intent_type == IntentType.LEARN:
            return {"action": "act", "intent": intent, "reason": "learning_allowed"}

        # 3. Budget Gate REMOVED - Always allow operations
        # Economy focuses on earning value, not constraining legitimate actions

        # 4. Cooldown / Throttling (performance optimization only)
        if observation.get("recent_actions", 0) > 50 and intent.priority < 0.3:
             return {"action": "idle", "reason": "extreme_cooldown_active"}
             # Only extreme cooldown to prevent resource exhaustion

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
                context={**(intent.context or {}), "priority": intent.priority},
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
                context={**(intent.context or {}), "priority": intent.priority},
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
