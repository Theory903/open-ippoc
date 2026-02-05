import os
import asyncio
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from .schemas import ActionCandidate, ModelMetadata

load_dotenv()

class TwoTowerEngine:
    """
    Implements the Two-Tower Cognitive Architecture with real LLM backends.
    """
    
    def __init__(self):
        # Configuration
        self.tower_a_model_name = os.getenv("TOWER_A_MODEL", "gemini-2.0-flash-exp")
        self.tower_b_model_name = os.getenv("TOWER_B_MODEL", "gemini-2.0-flash-thinking-exp-01-21")
        self.api_key = os.getenv("GOOGLE_API_KEY")
        
        self.risk_threshold = "medium"
        
        # Initialize Clients
        # In a real system, we'd use a factory based on TOWER_A_PROVIDER
        if not self.api_key:
            print("[WARN] GOOGLE_API_KEY not found. TwoTowerEngine running in Mock Mode.")
            self.llm_a = None
            self.llm_b = None
        else:
            self.llm_a = ChatGoogleGenerativeAI(model=self.tower_a_model_name, google_api_key=self.api_key, temperature=0.7)
            self.llm_b = ChatGoogleGenerativeAI(model=self.tower_b_model_name, google_api_key=self.api_key, temperature=0.2)
        
        # Model Market
        self.model_market: Dict[str, ModelMetadata] = {
            self.tower_a_model_name: ModelMetadata(
                model=self.tower_a_model_name,
                strengths=["speed", "cost"],
                weaknesses=["complex reasoning"],
                avg_cost=0.1,
                trust_score=0.8
            ),
            self.tower_b_model_name: ModelMetadata(
                model=self.tower_b_model_name,
                strengths=["reasoning", "coding"],
                weaknesses=["latency"],
                avg_cost=1.0,
                trust_score=0.95
            )
        }

    async def generate_impulse(self, context: str) -> ActionCandidate:
        """
        Tower A: Generates inner monologue, hypotheses, code drafts.
        """
        if not self.llm_a:
            return ActionCandidate(
                action="mock_explore", confidence=0.5, expected_cost=0.0, risk="low", requires_validation=False,
                payload={"thought": "Mock Impulse: No API Key provided."}
            )

        prompt = f"""
        You are Tower A (Impulse). 
        Context: {context}
        
        Generate a hypothesis or action.
        Format: Return ONLY a JSON object with keys: "action" (snake_case), "thought" (string), "risk" (low/medium/high).
        """
        
        try:
            # Simple structured output parsing (JsonOutputParser is better but keeping it raw for speed)
            response = await self.llm_a.ainvoke([HumanMessage(content=prompt)])
            # naive parsing
            import json
            content = response.content.strip()
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            
            data = json.loads(content)
            
            return ActionCandidate(
                action=data.get("action", "unknown"),
                # Heuristic: Higher confidence if specific thought + low risk
                confidence=0.8 if data.get("risk") == "low" and len(data.get("thought", "")) > 20 else 0.6,
                expected_cost=0.5,
                risk=data.get("risk", "low"),
                requires_validation=self._is_high_risk(data.get("risk", "low")),
                payload={"thought": data.get("thought", "")}
            )
        except Exception as e:
            print(f"[Tower A] Error: {e}")
            return ActionCandidate(
                action="error_fallback", confidence=0.0, expected_cost=0.0, risk="low", requires_validation=False,
                payload={"thought": "Failed to generate impulse."}
            )

    async def validate_action(self, candidate: ActionCandidate) -> bool:
        """
        Tower B: Validates risky actions.
        """
        if not self.llm_b:
            # Evolution: Log Pattern even in Mock Mode
            await self._log_pattern(candidate, "MOCK_YES", True)
            return True # Mock allow

        prompt = f"""
        You are Tower B (Validator).
        Proposed Action: {candidate.action}
        Risk: {candidate.risk}
        Details: {candidate.payload}
        
        Should this be executed?
        Return ONLY "YES" or "NO" followed by a reason.
        """
        
        try:
            response = await self.llm_b.ainvoke([HumanMessage(content=prompt)])
            content = response.content.strip().upper()
            approved = content.startswith("YES")
            
            # Evolution: Log Pattern for fine-tuning
            await self._log_pattern(candidate, content, approved)
            
            return approved
        except Exception as e:
            print(f"[Tower B] Error: {e}")
            # Evolution: Log Error Pattern
            await self._log_pattern(candidate, "ERROR", False)
            return False

    async def _log_pattern(self, candidate: ActionCandidate, validator_response: str, approved: bool):
        """
        Saves the Impulse -> Validation pair to build the 'Pattern Engine' dataset.
        """
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._log_pattern_sync, candidate, validator_response, approved)

    def _log_pattern_sync(self, candidate: ActionCandidate, validator_response: str, approved: bool):
        import json
        from datetime import datetime
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "impulse": candidate.dict(),
            "validator_response": validator_response,
            "approved": approved,
            "model_a": self.tower_a_model_name,
            "model_b": self.tower_b_model_name
        }
        
        try:
            with open("brain/data/patterns.jsonl", "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"[Evolution] Failed to log pattern: {e}")

    def select_model(self, task_type: str, risk_level: str) -> str:
        if self._is_high_risk(risk_level):
            return self.tower_b_model_name
        return self.tower_a_model_name

    def update_model_market(self, metadata: ModelMetadata):
        self.model_market[metadata.model] = metadata

    def _is_high_risk(self, risk_level: str) -> bool:
        levels = ["low", "medium", "high", "critical"]
        try:
            threshold_idx = levels.index(self.risk_threshold)
            current_idx = levels.index(risk_level)
            return current_idx >= threshold_idx
        except ValueError:
            return True
