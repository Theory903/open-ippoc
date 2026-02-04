from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import asyncio
from cortex.core.orchestrator import get_orchestrator
from cortex.core.tools.base import ToolInvocationEnvelope

# Initialize Orchestrator access (Singleton)
orchestrator = get_orchestrator()

class MemorizeInput(BaseModel):
    content: str = Field(description="The factual content or event to remember.")
    confidence: float = Field(default=0.8, description="How confident are you in this fact (0.0-1.0).")

@tool("memorize_fact", args_schema=MemorizeInput)
def memorize_fact(content: str, confidence: float = 0.8) -> str:
    """
    Stores a fact or event in long-term memory.
    Use this when you learn something new or need to remember user context.
    The memory will be consolidated and indexed automatically.
    """
    envelope = ToolInvocationEnvelope(
        tool_name="memory",
        domain="memory",
        action="store_episodic",
        context={"content": content, "confidence": confidence, "source": "langchain_tool"},
        risk_level="low",
        estimated_cost=0.5
    )
    try:
        result = orchestrator.invoke(envelope)
        return str(result.output)
    except Exception as e:
        return f"Tool Execution Failed: {str(e)}"

class DelegateInput(BaseModel):
    action: str = Field(description="The specific action identifier (e.g., 'git_clone', 'web_search').")
    params: Dict[str, Any] = Field(description="Parameters required for the action.")

@tool("delegate_to_body", args_schema=DelegateInput)
def delegate_to_body(action: str, params: Dict[str, Any]) -> str:
    """
    Delegates a physical action to the Body (Rust Node).
    Use this for: executing shell commands, file I/O, crypto transactions, or networking.
    The Brain CANNOT do these things directly.
    """
    envelope = ToolInvocationEnvelope(
        tool_name="body",
        domain="body",
        action="execute_command", # Mapping generic delegate to command execution
        context={"command": action, "params": params, "source": "langchain_tool"},
        risk_level="medium",
        estimated_cost=0.2
    )
    try:
        result = orchestrator.invoke(envelope)
        return str(result.output)
    except Exception as e:
         return f"Tool Execution Failed: {str(e)}"

class QueryMemoryInput(BaseModel):
    query: str = Field(description="The question or topic to search for in memory.")

@tool("query_memory", args_schema=QueryMemoryInput)
def query_memory(query: str) -> str:
    """
    Searches the Hippocampus (Long-term Memory) for facts, events, and skills.
    Use this before answering complex questions to ground your response in known facts.
    """
    envelope = ToolInvocationEnvelope(
        tool_name="memory",
        domain="memory",
        action="retrieve",
        context={"query": query, "source": "langchain_tool"},
        risk_level="low",
        estimated_cost=0.1
    )
    try:
        result = orchestrator.invoke(envelope)
        return str(result.output)
    except Exception as e:
         return f"Tool Execution Failed: {str(e)}"


