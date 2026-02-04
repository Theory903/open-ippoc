# brain/core/orchestrator.py

import asyncio
import json
import logging
import os
import time
from contextvars import ContextVar
from typing import Dict, Optional, Tuple, Any
from brain.core.exceptions import ToolExecutionError, SecurityViolation, BudgetExceeded
from brain.core.economy import get_economy
from brain.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult

# Configure Logging
logger = logging.getLogger("IPPOC.Orchestrator")

_SPINE_ACTIVE: ContextVar[bool] = ContextVar("ippoc_spine_active", default=False)


def require_spine() -> None:
    """
    Guard to prevent tool execution outside the ToolOrchestrator spine.
    """
    if not _SPINE_ACTIVE.get():
        raise SecurityViolation("Tool execution bypassed ToolOrchestrator")


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
        self.economy = get_economy()
        self.tool_budgets: Dict[str, float] = {}
        self.tenant_budgets: Dict[str, float] = {}
        self.domain_allowlist = set(filter(None, os.getenv("ORCHESTRATOR_DOMAIN_ALLOWLIST", "").split(",")))
        self.domain_denylist = set(filter(None, os.getenv("ORCHESTRATOR_DOMAIN_DENYLIST", "").split(",")))
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.idempotency_cache: Dict[str, Tuple[float, ToolResult]] = {}
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
        cached = self._check_idempotency(envelope)
        if cached is not None:
            return cached
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
        
        token = _SPINE_ACTIVE.set(True)
        try:
            # 5. Execution (Atomic)
            result = tool.execute(envelope)
            # 6. Accounting (Post-Execution)
            final_cost = result.cost_spent if result.cost_spent > 0 else estimated_cost
            self.economy.spend(final_cost, tool_name=tool_name)
            # Ensure audit trail counts as memory write
            self._audit_action(envelope, result, final_cost, None)
            if not result.memory_written:
                result.memory_written = True
            logger.info(f"SUCCESS: {tool_name} | Cost: {final_cost} | Written: {result.memory_written}")
            self._store_idempotency(envelope, result)
            return result
        except Exception as e:
            logger.error(f"FAILURE: {tool_name} | Error: {str(e)}")
            self._audit_action(envelope, None, estimated_cost, str(e))
            raise ToolExecutionError(tool_name, str(e))
        finally:
            _SPINE_ACTIVE.reset(token)

    async def invoke_async(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        """
        Async invoke with timeout, retries, and circuit breaker.
        """
        cached = self._check_idempotency(envelope)
        if cached is not None:
            return cached
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

        token = _SPINE_ACTIVE.set(True)
        try:
            while attempt <= max_retries:
                try:
                    if timeout:
                        result = await asyncio.wait_for(asyncio.to_thread(tool.execute, envelope), timeout=timeout)
                    else:
                        result = await asyncio.to_thread(tool.execute, envelope)
                    breaker.record_success()

                    final_cost = result.cost_spent if result.cost_spent > 0 else estimated_cost
                    self.economy.spend(final_cost, tool_name=tool_name)
                    self._audit_action(envelope, result, final_cost, None)
                    if not result.memory_written:
                        result.memory_written = True
                    self._store_idempotency(envelope, result)
                    return result
                except asyncio.TimeoutError as e:
                    breaker.record_failure()
                    last_error = e
                    if attempt >= max_retries:
                        self._audit_action(envelope, None, estimated_cost, "Execution timeout")
                        raise ToolExecutionError(tool_name, "Execution timeout")
                except Exception as e:
                    breaker.record_failure()
                    last_error = e
                    if attempt >= max_retries or not self._is_retryable(e):
                        self._audit_action(envelope, None, estimated_cost, str(e))
                        raise ToolExecutionError(tool_name, str(e))
                attempt += 1
        finally:
            _SPINE_ACTIVE.reset(token)

        raise ToolExecutionError(tool_name, str(last_error) if last_error else "Execution failed")

    def _check_permissions(self, envelope: ToolInvocationEnvelope) -> None:
        """
        Verify if the caller is allowed to use this tool.
        """
        if os.getenv("ORCHESTRATOR_KILL_SWITCH", "false").lower() == "true":
            raise SecurityViolation("Kill switch enabled")
        tool_allow = set(filter(None, os.getenv("ORCHESTRATOR_TOOL_ALLOWLIST", "").split(",")))
        tool_deny = set(filter(None, os.getenv("ORCHESTRATOR_TOOL_DENYLIST", "").split(",")))
        if tool_allow and envelope.tool_name not in tool_allow:
            raise SecurityViolation(f"Tool '{envelope.tool_name}' not allowed")
        if envelope.tool_name in tool_deny:
            raise SecurityViolation(f"Tool '{envelope.tool_name}' denied")
        # TODO: Connect to explicit Policy Engine / ACLs
        # For now, simplistic safety check:
        max_risk = os.getenv("ORCHESTRATOR_MAX_RISK", "high").lower()
        risk_order = {"low": 0, "medium": 1, "high": 2}
        if risk_order.get(envelope.risk_level, 0) > risk_order.get(max_risk, 2):
            raise SecurityViolation(f"Risk level '{envelope.risk_level}' exceeds policy")
        if envelope.risk_level == "high" and not envelope.requires_validation:
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
        # 0. Free Tools Bypass
        if estimated_cost <= 0:
            return

        snapshot = self.economy.snapshot()
        emergency = bool(envelope.context.get("emergency")) if envelope.context else False
        priority = float(envelope.context.get("priority", 0.0)) if envelope.context else 0.0
        
        # Check throttling (unless priority is Critical/Emergency)
        if priority <= 0.8 and self.economy.should_throttle(tool_name):
            raise BudgetExceeded(estimated_cost, snapshot["budget"])
            
        if estimated_cost > snapshot["budget"]:
            # Critical Priority bypasses hard budget stop?
            if emergency or tool_name == "maintainer" or priority > 0.8:
                return
            raise BudgetExceeded(estimated_cost, snapshot["budget"])

        if tool_name in self.tool_budgets and estimated_cost > self.tool_budgets[tool_name]:
            raise BudgetExceeded(estimated_cost, self.tool_budgets[tool_name])

        if envelope.tenant and envelope.tenant in self.tenant_budgets:
            if estimated_cost > self.tenant_budgets[envelope.tenant]:
                raise BudgetExceeded(estimated_cost, self.tenant_budgets[envelope.tenant])

    def get_budget(self) -> Dict[str, float]:
        return self.economy.snapshot()

    def get_reputation(self, tool_name: str) -> Dict[str, Any]:
        """
        Returns the economic reputation of a tool.
        """
        stats = self.economy.get_tool_stats(tool_name)
        throttled = self.economy.should_throttle(tool_name)
        return {
            "tool": tool_name,
            "calls": stats.calls,
            "avg_cost": stats.total_spent / stats.calls if stats.calls else 0.0,
            "avg_value": stats.total_value / stats.calls if stats.calls else 0.0,
            "roi": stats.roi,
            "status": "throttled" if throttled else "active"
        }

    def _is_retryable(self, error: Exception) -> bool:
        return isinstance(error, (TimeoutError, ToolExecutionError))

    def _check_idempotency(self, envelope: ToolInvocationEnvelope) -> Optional[ToolResult]:
        key = envelope.idempotency_key
        if not key:
            return None
        ttl = int(os.getenv("ORCHESTRATOR_IDEMPOTENCY_TTL", "3600"))
        cached = self.idempotency_cache.get(key)
        if not cached:
            return None
        ts, result = cached
        if time.time() - ts > ttl:
            self.idempotency_cache.pop(key, None)
            return None
        return result

    def _store_idempotency(self, envelope: ToolInvocationEnvelope, result: ToolResult) -> None:
        key = envelope.idempotency_key
        if not key:
            return
        self.idempotency_cache[key] = (time.time(), result)

    def _audit_action(self, envelope: ToolInvocationEnvelope, result: Optional[ToolResult], cost: float, error: Optional[str]) -> None:
        path = os.getenv("ORCHESTRATOR_AUDIT_PATH", "data/action_log.jsonl")
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            payload = {
                "ts": time.time(),
                "tool": envelope.tool_name,
                "domain": envelope.domain,
                "action": envelope.action,
                "caller": envelope.caller,
                "tenant": envelope.tenant,
                "source": envelope.source,
                "risk_level": envelope.risk_level,
                "estimated_cost": envelope.estimated_cost,
                "final_cost": cost,
                "success": result.success if result else False,
                "error": error,
                "reason": envelope.context.get("reason") if envelope.context else None,
            }
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception:
            # Never block on audit failure
            pass

# Global Singleton Accessor
_orchestrator = ToolOrchestrator()

def get_orchestrator() -> ToolOrchestrator:
    return _orchestrator
