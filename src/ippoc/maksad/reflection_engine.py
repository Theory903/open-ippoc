import asyncio
import time
from typing import List, Optional, Dict, Any
from ippoc.maksad.intent_engine import get_intent_engine
import requests
import os
from .cognitive_bus import emit_thought

class ReflectionEngine:
    def __init__(self, soma_url: str):
        self.soma_url = soma_url
        self.last_reflection_time = time.time()

    async def audit_recent_memories(self):
        """
        Polls Soma for recent memories and analyzes them for unresolved goals or patterns.
        """
        await emit_thought("info", "[Reflection] Auditing biological memory bank...")
        try:
            # Query Soma for the last 20 memories
            resp = requests.get(f"{self.soma_url}/v1/memory/recent?limit=20", timeout=5)
            if resp.ok:
                results = resp.json().get("results", [])
                for mem in results:
                    content = mem.get("content", "").lower()
                    # Real heuristic: If memory contains 'todo', 'fix', or 'investigate'
                    if any(x in content for x in ["todo", "fix", "investigate", "error"]):
                        print(f"[Reflection] Cognitive Gap Detected: {content}")
                        await get_intent_engine().add_intent(
                            goal=f"Follow up on cognitive gap: {content[:50]}...",
                            urgency=0.6
                        )
            else:
                pass # Silently ignore non-200 from Soma (might be starting up)
        except Exception:
            print("[Reflection] Memory unavailable - skipping audit")
            return

    async def reflect_on_failures(self):
        """
        Scans the execution ledger for recent failures and creates corrective intents.
        """
        print("[Reflection] Auditing execution failures...")
        from ippoc.cortex.core.ledger import get_ledger
        ledger = get_ledger()
        try:
            # Only SqlLedger supports list_recent_failures currently
            if hasattr(ledger, "list_recent_failures"):
                failures = await ledger.list_recent_failures(limit=5)
                for f in failures:
                    print(f"[Reflection] Repair Intent Created for failure: {f['tool_name']}")
                    await get_intent_engine().add_intent(
                        goal=f"Analyze and repair failure in {f['tool_name']}: {f['error_message'][:100]}", 
                        urgency=0.9
                    )
        except Exception as e:
            print(f"[Reflection] Failure audit failed: {e}")

    async def run_reflection_cycle(self):
        """
        The main cognitive audit loop with Novelty Detection.
        """
        print("[Reflection] Beginning self-analysis cycle...")
        
        # 1. Look for patterns/gaps in memory
        await self.audit_recent_memories()
        
        # 2. Look for operational failures
        await self.reflect_on_failures()
        
        # 3. Curiosity: Propose exploratory task if idle or repetitive
        active_intents = await get_intent_engine().get_active_intents()
        
        # Novelty Check: If we have many intents with the same goal, novelty is low
        goals = [i.goal for i in active_intents]
        unique_goals = set(goals)
        novelty_score = len(unique_goals) / len(goals) if goals else 1.0
        
        if not active_intents or novelty_score < 0.5:
            reason = "idle" if not active_intents else "repetitive patterns"
            print(f"[Reflection] System is {reason}. Novelty Score: {novelty_score:.2f}. Proposing curiosity intent.")
            
            # Deterministic Curiosity: Select goal based on day index (no randomness)
            curiosity_goals = [
                "Audit local network for new IPPOC nodes",
                "Scan filesystem for configuration drift",
                "Review recent memory summaries for emerging themes",
                "Optimize internal tool calling latency"
            ]
            day_index = int(time.time() / 86400) % len(curiosity_goals)
            goal = curiosity_goals[day_index]
            
            await get_intent_engine().add_intent(
                goal=f"Autonomous Curiosity: {goal}", 
                urgency=0.2,
                ttl=1800
            )

        self.last_reflection_time = time.time()

    async def main_loop(self, interval: int = 300):
        print(f"[Reflection] Engine started (audit every {interval}s)")
        while True:
            try:
                await self.run_reflection_cycle()
            except Exception as e:
                print(f"[Reflection] Cycle error: {e}")
            await asyncio.sleep(interval)

_reflection_instance: Optional[ReflectionEngine] = None

def get_reflection_engine() -> ReflectionEngine:
    global _reflection_instance
    if _reflection_instance is None:
        soma_url = os.getenv("IPPOC_SOMA_URL", "http://localhost:8081")
        _reflection_instance = ReflectionEngine(soma_url)
    return _reflection_instance
