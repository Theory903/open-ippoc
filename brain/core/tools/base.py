# brain/core/tools/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

class ToolInvocationEnvelope(BaseModel):
    """
    Standard envelope for all tool calls in IPPOC.
    Ensures intent, context, and risk are explicit.
    """
    tool_name: str = Field(description="The unique identifier of the tool (e.g., 'memory.store_episodic')")
    domain: Literal["memory", "body", "evolution", "cognition", "economy", "social", "simulation"] = Field(description="The owning domain")
    action: str = Field(description="The specific action being requested")
    
    context: Dict[str, Any] = Field(default_factory=dict, description="Contextual metadata (caller, reason, etc.)")
    risk_level: Literal["low", "medium", "high"] = Field(default="low", description="Risk assessment of the action")
    estimated_cost: float = Field(default=0.0, description="Estimated economic cost (tokens/credits)")
    
    requires_validation: bool = Field(default=False, description="If True, requires explicit approval/validation step")
    rollback_allowed: bool = Field(default=False, description="If True, the action must support rollback")

class ToolResult(BaseModel):
    """
    Standardized result from a tool execution.
    """
    success: bool
    output: Optional[Any] = None
    
    cost_spent: float = 0.0
    memory_written: bool = False
    
    rollback_token: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)

class IPPOC_Tool(ABC):
    """
    Abstract Base Class for all IPPOC tools.
    Domain adapters must inherit from this.
    """
    def __init__(self, name: str, domain: str):
        self.name = name
        self.domain = domain

    @abstractmethod
    def estimate_cost(self, envelope: ToolInvocationEnvelope) -> float:
        """
        Calculate the cost of this operation before execution.
        """
        pass

    @abstractmethod
    def execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        """
        Execute the tool logic.
        Must return a ToolResult.
        Must raise ToolExecutionError on failure.
        """
        pass
