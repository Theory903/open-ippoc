# brain/core/orchestrator.py

import logging
from typing import Dict, Optional, Type
from brain.core.exceptions import ToolExecutionError, SecurityViolation, BudgetExceeded
from brain.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult, ToolInvocationEnvelope

# Configure Logging
logger = logging.getLogger("IPPOC.Orchestrator")

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
        self.current_budget: float = 1000.0  # Startup credit
        self.initialized = True
        logger.info("ToolOrchestrator initialized.")

    def register(self, tool: IPPOC_Tool) -> None:
        """
        Register a new tool capability.
        """
        if tool.name in self.tools:
            logger.warning(f"Overwriting existing tool registration: {tool.name}")
        
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name} (Domain: {tool.domain})")

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
        if estimated_cost > self.current_budget:
            raise BudgetExceeded(estimated_cost, self.current_budget)
        
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

# Global Singleton Accessor
_orchestrator = ToolOrchestrator()

def get_orchestrator() -> ToolOrchestrator:
    return _orchestrator
