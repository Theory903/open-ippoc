# brain/core/orchestrator.py

import asyncio
import json
import logging
import os
import time
from typing import Dict, Optional
from brain.core.exceptions import ToolExecutionError, SecurityViolation, BudgetExceeded
from brain.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult

# Configure Logging
logger = logging.getLogger("IPPOC.Orchestrator")


class CircuitBreaker:
    def __init__(self, threshold: int = 5, reset_seconds: int = 30):
        self.threshold = threshold
        self.reset_seconds = reset_seconds
        self.failure_count = 0
        self.open_until: Optional[float] = None

    def record_success(self) -> None:
        self.failure_count = 0
        self.open_until = None

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.threshold:
            self.open_until = time.time() + self.reset_seconds

    def allow(self) -> bool:
        if self.open_until is None:
            return True
        if time.time() >= self.open_until:
            self.failure_count = 0
            self.open_until = None
            return True
        return False

class ToolOrchestrator:
    """
    The Spine of IPPOC.
    Central governance for all tool executions.
    Singleton pattern recommended.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolOrchestrator, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        
        self.tools: Dict[str, IPPOC_Tool] = {}
        self.current_budget: float = float(os.getenv("ORCHESTRATOR_BUDGET", "1000.0"))
        self.tool_budgets: Dict[str, float] = {}
        self.tenant_budgets: Dict[str, float] = {}
        self.domain_allowlist = set(filter(None, os.getenv("ORCHESTRATOR_DOMAIN_ALLOWLIST", "").split(",")))
        self.domain_denylist = set(filter(None, os.getenv("ORCHESTRATOR_DOMAIN_DENYLIST", "").split(",")))
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._load_budget_overrides()
        self.initialized = True
        logger.info("ToolOrchestrator initialized.")

    def register(self, tool: IPPOC_Tool) -> None:
        """
        Register a new tool capability.
        """
        if tool.name in self.tools:
            logger.warning(f"Overwriting existing tool registration: {tool.name}")
        
        self.tools[tool.name] = tool
        if tool.name not in self.circuit_breakers:
            self.circuit_breakers[tool.name] = CircuitBreaker()
        logger.info(f"Registered tool: {tool.name} (Domain: {tool.domain})")

    def _load_budget_overrides(self) -> None:
        tool_budget_json = os.getenv("ORCHESTRATOR_TOOL_BUDGETS")
        tenant_budget_json = os.getenv("ORCHESTRATOR_TENANT_BUDGETS")
        if tool_budget_json:
            try:
                self.tool_budgets = {k: float(v) for k, v in json.loads(tool_budget_json).items()}
            except Exception:
                logger.warning("Failed to parse ORCHESTRATOR_TOOL_BUDGETS")
        if tenant_budget_json:
            try:
                self.tenant_budgets = {k: float(v) for k, v in json.loads(tenant_budget_json).items()}
            except Exception:
                logger.warning("Failed to parse ORCHESTRATOR_TENANT_BUDGETS")

    def invoke(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        """
        The Universal Execution Path.
        All actions must pass through here.
        """
        tool_name = envelope.tool_name
        
        # 1. Validation: Does tool exist?
        if tool_name not in self.tools:
            raise ToolExecutionError(tool_name, "Tool not registered.")
        
        tool = self.tools[tool_name]
        
        # 2. Permission Check (Stub for Policy Engine)
        self._check_permissions(envelope)
        
        # 3. Cost Metering (Pre-Check)
        estimated_cost = tool.estimate_cost(envelope)
        self._check_budget(envelope, tool_name, estimated_cost)
        
        # 4. Audit Log (Pre-Execution)
        logger.info(f"INVOKE: {tool_name} | Caller: {envelope.context.get('caller', 'unknown')} | Intent: {envelope.action}")
        
        try:
            # 5. Execution (Atomic)
            result = tool.execute(envelope)
            
            # 6. Accounting (Post-Execution)
            # Use actual cost if provided by result, else estimate
            final_cost = result.cost_spent if result.cost_spent > 0 else estimated_cost
            self.current_budget -= final_cost
            
            # 7. Audit Log (Post-Execution)
            logger.info(f"SUCCESS: {tool_name} | Cost: {final_cost} | Written: {result.memory_written}")
            
            return result
            
        except Exception as e:
            logger.error(f"FAILURE: {tool_name} | Error: {str(e)}")
            raise ToolExecutionError(tool_name, str(e))

    async def invoke_async(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        """
        Async invoke with timeout, retries, and circuit breaker.
        """
        tool_name = envelope.tool_name
        if tool_name not in self.tools:
            raise ToolExecutionError(tool_name, "Tool not registered.")

        tool = self.tools[tool_name]
        self._check_permissions(envelope)
        estimated_cost = tool.estimate_cost(envelope)
        self._check_budget(envelope, tool_name, estimated_cost)

        breaker = self.circuit_breakers.get(tool_name) or CircuitBreaker()
        self.circuit_breakers[tool_name] = breaker
        if not breaker.allow():
            raise ToolExecutionError(tool_name, "Circuit breaker open")

        max_retries = int(envelope.context.get("max_retries", 0) if envelope.context else 0)
        timeout_ms = envelope.deadline_ms or int(envelope.context.get("timeout_ms", 0) if envelope.context else 0)
        if not timeout_ms:
            timeout_ms = int(os.getenv("ORCHESTRATOR_DEADLINE_MS", "0") or 0)
        timeout = timeout_ms / 1000 if timeout_ms else None

        attempt = 0
        last_error: Optional[Exception] = None

        while attempt <= max_retries:
            try:
                if timeout:
                    result = await asyncio.wait_for(asyncio.to_thread(tool.execute, envelope), timeout=timeout)
                else:
                    result = await asyncio.to_thread(tool.execute, envelope)
                breaker.record_success()

                final_cost = result.cost_spent if result.cost_spent > 0 else estimated_cost
                self.current_budget -= final_cost
                return result
            except asyncio.TimeoutError as e:
                breaker.record_failure()
                last_error = e
                if attempt >= max_retries:
                    raise ToolExecutionError(tool_name, "Execution timeout")
            except Exception as e:
                breaker.record_failure()
                last_error = e
                if attempt >= max_retries or not self._is_retryable(e):
                    raise ToolExecutionError(tool_name, str(e))
            attempt += 1

        raise ToolExecutionError(tool_name, str(last_error) if last_error else "Execution failed")

    def _check_permissions(self, envelope: ToolInvocationEnvelope) -> None:
        """
        Verify if the caller is allowed to use this tool.
        """
        # TODO: Connect to explicit Policy Engine / ACLs
        # For now, simplistic safety check:
        if envelope.risk_level == "high" and not envelope.requires_validation:
             # Just a warning for now, or could enforce stricter rules
             logger.warning(f"High risk action invoked without validation flag: {envelope.tool_name}")
        
        # Placeholder for 'sandbox' enforcement
        if envelope.domain == "evolution" and envelope.context.get("environment") == "stable":
             if not envelope.requires_validation:
                 raise SecurityViolation("Stable channel evolution requires manual validation.")

        if self.domain_allowlist and envelope.domain not in self.domain_allowlist:
            raise SecurityViolation(f"Domain '{envelope.domain}' not allowed")
        if envelope.domain in self.domain_denylist:
            raise SecurityViolation(f"Domain '{envelope.domain}' denied")

    def _check_budget(self, envelope: ToolInvocationEnvelope, tool_name: str, estimated_cost: float) -> None:
        if estimated_cost > self.current_budget:
            raise BudgetExceeded(estimated_cost, self.current_budget)

        if tool_name in self.tool_budgets and estimated_cost > self.tool_budgets[tool_name]:
            raise BudgetExceeded(estimated_cost, self.tool_budgets[tool_name])

        if envelope.tenant and envelope.tenant in self.tenant_budgets:
            if estimated_cost > self.tenant_budgets[envelope.tenant]:
                raise BudgetExceeded(estimated_cost, self.tenant_budgets[envelope.tenant])

    def _is_retryable(self, error: Exception) -> bool:
        return isinstance(error, (TimeoutError, ToolExecutionError))

# Global Singleton Accessor
_orchestrator = ToolOrchestrator()

def get_orchestrator() -> ToolOrchestrator:
    return _orchestrator
