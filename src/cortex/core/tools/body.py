# brain/core/tools/body.py
# @cognitive - Enhanced Body Adapter with OpenClaw Integration

import aiohttp
import asyncio
import os
import nest_asyncio
from typing import Dict, Any
from cortex.core.tools.base import IPPOC_Tool, ToolInvocationEnvelope, ToolResult
from cortex.core.exceptions import ToolExecutionError
from cortex.gateway.openclaw_adapter import send_directive_to_kernel, get_kernel_status
from cortex.gateway.proprioception_scanner import get_scanner

BODY_URL = os.getenv("BODY_URL", "http://localhost:9000")
BODY_ALLOWLIST = set(filter(None, os.getenv("BODY_ALLOWLIST", "").split(",")))
BODY_ENFORCE_ALLOWLIST = os.getenv("BODY_ENFORCE_ALLOWLIST", "false").lower() == "true"

# Enhanced tool registry with proprioceptive awareness
TOOL_REGISTRY = {
    # Native body tools (Rust)
    "execute_command": {"cost": 0.2, "domain": "system"},
    "network_request": {"cost": 0.3, "domain": "network"},
    "file_operation": {"cost": 0.1, "domain": "filesystem"},
    
    # OpenClaw skill proxies (dynamically populated)
    # These will be populated during bootstrap from proprioception scan
}

class BodyAdapter(IPPOC_Tool):
    """
    Enhanced Body Adapter with OpenClaw Integration.
    Prevents hallucination by leveraging proprioceptive skill awareness.
    """
    def __init__(self):
        super().__init__(name="body", domain="body")
        self._populate_openclaw_tools()

    def _populate_openclaw_tools(self):
        """Populate tool registry with discovered OpenClaw skills"""
        try:
            scanner = get_scanner()
            tool_defs = scanner.to_tool_definitions()
            TOOL_REGISTRY.update(tool_defs)
            print(f"[BodyAdapter] Registered {len(tool_defs)} OpenClaw skills")
        except Exception as e:
            print(f"[BodyAdapter] Failed to populate OpenClaw tools: {e}")

    def estimate_cost(self, envelope: ToolInvocationEnvelope) -> float:
        """Enhanced cost estimation with proprioceptive awareness"""
        action = envelope.action
        
        # Check if this is an OpenClaw skill
        if action.startswith("openclaw_"):
            skill_name = action.replace("openclaw_", "")
            # Get actual energy cost from proprioception map
            scanner = get_scanner()
            skills = scanner.discovered_skills
            if skill_name in skills:
                return skills[skill_name].energy_cost
            
        # Fall back to registry or default
        if action in TOOL_REGISTRY:
            return TOOL_REGISTRY[action].get("cost", 0.2)
        
        # Default cost for unknown actions
        return 0.5

    def execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        """Execute with proprioceptive awareness to prevent hallucination"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop:
            nest_asyncio.apply()
            return loop.run_until_complete(self._async_execute(envelope))

        return asyncio.run(self._async_execute(envelope))

    async def _async_execute(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        """Enhanced async execution with OpenClaw integration"""
        action = envelope.action
        
        # 1. Conscious Override Check - Canon enforcement
        if self._violates_canon(envelope):
            return ToolResult(
                success=False,
                output="Action refused: Canon violation detected",
                error_code="canon_violation",
                warnings=["Conscious override prevented harmful action"]
            )
        
        # 2. Proprioception Check - Prevent hallucination
        if action.startswith("openclaw_"):
            return await self._execute_openclaw_skill(envelope)
        
        # 3. Native body execution
        if action == "execute_command":
            return await self._remote_exec(envelope)
        elif action == "economy_balance":
            return await self._get_balance()
        elif action == "network_request":
            return await self._network_request(envelope)
        
        # 4. Fallback generic execution
        return await self._remote_exec(envelope)
    
    def _violates_canon(self, envelope: ToolInvocationEnvelope) -> bool:
        """Check if action violates IPPOC Canon"""
        from cortex.core.canon import violates_canon
        from cortex.core.intents import Intent
        
        # Create dummy intent for canon check
        dummy_intent = Intent(
            description=envelope.context.get("description", envelope.action),
            context=envelope.context,
            intent_type="SERVE",
            source="body_tool",
            priority=0.0
        )
        
        return violates_canon(dummy_intent)
    
    async def _execute_openclaw_skill(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        """Execute OpenClaw skill through proprioceptive bridge"""
        skill_name = envelope.action.replace("openclaw_", "")
        
        # Verify kernel connection
        kernel_status = get_kernel_status()
        if not kernel_status.connected:
            return ToolResult(
                success=False,
                output="OpenClaw kernel disconnected",
                error_code="kernel_disconnected",
                warnings=[f"Cannot execute {skill_name}: Kernel offline"]
            )
        
        # Prepare directive for OpenClaw
        directive = {
            "skill": skill_name,
            "action": envelope.action,
            "parameters": envelope.context,
            "timeout": envelope.deadline_ms or 30000,
            "priority": envelope.context.get("priority", 0.5)
        }
        
        try:
            # Send to OpenClaw kernel
            result = await send_directive_to_kernel(directive)
            
            return ToolResult(
                success=result.get("status") == "success",
                output=result.get("result", result),
                cost_spent=self.estimate_cost(envelope),
                memory_written=True,  # Skill execution implies learning
                warnings=result.get("warnings", [])
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output=f"OpenClaw skill execution failed: {str(e)}",
                error_code="execution_failed",
                warnings=[str(e)]
            )

    async def _remote_exec(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        """Execute command on native body (Rust node)"""
        cmd = envelope.context.get("command") or envelope.action
        params = envelope.context.get("params", {})

        if (envelope.sandboxed or BODY_ENFORCE_ALLOWLIST) and BODY_ALLOWLIST:
            if cmd not in BODY_ALLOWLIST:
                raise ToolExecutionError(envelope.tool_name, f"Command not allowed: {cmd}")
        
        payload = {
            "action": cmd,
            "params": params,
            "source": envelope.context.get("source", "tool_orchestrator")
        }
        headers = {}
        internal_key = os.getenv("IPPOC_INTERNAL_KEY")
        if internal_key:
            headers["X-IPPOC-Key"] = internal_key

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{BODY_URL}/v1/execute", json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        return ToolResult(
                            success=True,
                            output=text,
                            cost_spent=0.2
                        )
                    else:
                        return ToolResult(
                            success=False,
                            output=f"Body returned {resp.status}",
                            warnings=["Body rejection"]
                        )
            except Exception as e:
                raise ToolExecutionError(envelope.tool_name, f"Body Connection Failed: {e}")

    async def _get_balance(self) -> ToolResult:
        """Get economy balance from body"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{BODY_URL}/v1/economy/balance") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return ToolResult(
                            success=True,
                            output=data,
                            cost_spent=0.1
                        )
                    return ToolResult(
                        success=False,
                        output=f"Balance check failed: {resp.status}",
                        warnings=[f"HTTP {resp.status}"]
                    )
            except Exception as e:
                raise ToolExecutionError("body", f"Body Connection Failed: {e}")
                
    async def _network_request(self, envelope: ToolInvocationEnvelope) -> ToolResult:
        """Execute network request through body"""
        url = envelope.context.get("url")
        method = envelope.context.get("method", "GET")
        
        if not url:
            raise ToolExecutionError(envelope.tool_name, "Missing 'url' in context")
            
        payload = {
            "url": url,
            "method": method,
            "headers": envelope.context.get("headers", {}),
            "body": envelope.context.get("body")
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{BODY_URL}/v1/network/request", json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return ToolResult(
                            success=True,
                            output=data,
                            cost_spent=0.3
                        )
                    else:
                        return ToolResult(
                            success=False,
                            output=f"Network request failed: {resp.status}",
                            warnings=[f"HTTP {resp.status}"]
                        )
            except Exception as e:
                raise ToolExecutionError(envelope.tool_name, f"Network Request Failed: {e}")
