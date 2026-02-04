# brain/gateway/openclaw_adapter.py
# @cognitive - OpenClaw → IPPOC Adapter (Minimal Version)

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from cortex.gateway.openclaw_mapper import map_openclaw_to_intent
from cortex.gateway.openclaw_guard import guard_openclaw_request
from cortex.gateway.proprioception_scanner import get_scanner
from cortex.core.autonomy import AutonomyController
from cortex.core.exceptions import ToolExecutionError

# Configure logging
logger = logging.getLogger("IPPOC.OpenClawAdapter")

@dataclass
class KernelStatus:
    connected: bool
    last_heartbeat: Optional[datetime]
    version: str
    skills_available: int
    error_count: int

_controller = None
_kernel_status = KernelStatus(
    connected=False,
    last_heartbeat=None,
    version="unknown",
    skills_available=0,
    error_count=0
)

# Configuration
OPENCLAW_GATEWAY_URL = "http://localhost:3000"
HEARTBEAT_INTERVAL = 30
TIMEOUT_SECONDS = 30

async def initialize_synapse_bridge():
    """Initialize the connection to OpenClaw Kernel"""
    global _kernel_status
    
    logger.info("[Synapse] Initializing OpenClaw Bridge...")
    
    # 1. Scan available skills for proprioception
    try:
        scanner = get_scanner()
        skills = scanner.scan_skills()
        _kernel_status.skills_available = len(skills)
        logger.info(f"[Synapse] Proprioception mapped {len(skills)} skills")
    except Exception as e:
        logger.error(f"[Synapse] Proprioception scan failed: {e}")
        
    # 2. Establish initial connection
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)) as session:
            async with session.get(f"{OPENCLAW_GATEWAY_URL}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    _kernel_status.connected = True
                    _kernel_status.last_heartbeat = datetime.now()
                    _kernel_status.version = data.get("version", "unknown")
                    logger.info(f"[Synapse] Connected to OpenClaw v{_kernel_status.version}")
                    return True
    except Exception as e:
        logger.error(f"[Synapse] Failed to connect to OpenClaw: {e}")
        _kernel_status.error_count += 1
        return False

def get_kernel_status() -> KernelStatus:
    """Get current kernel connection status"""
    return _kernel_status

def get_controller() -> AutonomyController:
    global _controller
    if _controller is None:
        _controller = AutonomyController()
    return _controller

async def handle_openclaw_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    The ONLY entry point OpenClaw is allowed to call.
    """
    global _kernel_status
    
    try:
        # 1. Update heartbeat
        _kernel_status.last_heartbeat = datetime.now()
        
        # 2. Guardrail
        guard_openclaw_request(payload)

        action_type = payload.get("action_type")
        action_description = payload.get("description", "unknown action")

        # 3. Map to IPPOC Intent
        intent = map_openclaw_to_intent(payload)
        
        # 4. Proprioception Check
        scanner = get_scanner()
        matching_skills = scanner.find_matching_skills(action_description)
        
        if matching_skills:
            intent.context = intent.context or {}
            intent.context["available_skills"] = [s.name for s in matching_skills]
            intent.context["lowest_energy_cost"] = min(s.energy_cost for s in matching_skills)
            logger.debug(f"[Proprioception] Found {len(matching_skills)} matching skills")

        # 5. Inject intent into IPPOC
        controller = get_controller()
        controller.intent_stack.add(intent)

        # 6. Run cognitive cycle
        result = await controller.run_cycle()

        # 7. Return response
        response = {
            "status": result.get("status"),
            "result": result.get("result"),
            "reason": result.get("reason"),
            "intent_id": getattr(intent, 'intent_id', 'unknown'),
            "timestamp": datetime.now().isoformat()
        }
        
        return response
        
    except PermissionError as e:
        _kernel_status.error_count += 1
        logger.warning(f"[Synapse] Permission denied: {e}")
        return {
            "status": "refused",
            "error": str(e),
            "reason": "guard_rejection",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        _kernel_status.error_count += 1
        logger.error(f"[Synapse] Adapter crash: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "reason": "adapter_crash",
            "timestamp": datetime.now().isoformat()
        }

async def send_directive_to_kernel(directive: Dict[str, Any]) -> Dict[str, Any]:
    """Send directive FROM IPPOC TO OpenClaw"""
    global _kernel_status
    
    if not _kernel_status.connected:
        raise ToolExecutionError("openclaw", "Kernel disconnected")
        
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)) as session:
            async with session.post(
                f"{OPENCLAW_GATEWAY_URL}/directive",
                json=directive,
                headers={"Content-Type": "application/json"}
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    _kernel_status.last_heartbeat = datetime.now()
                    return result
                else:
                    error_text = await resp.text()
                    raise ToolExecutionError("openclaw", f"Kernel returned {resp.status}: {error_text}")
    except Exception as e:
        _kernel_status.connected = False
        _kernel_status.error_count += 1
        raise ToolExecutionError("openclaw", f"Connection failed: {e}")

async def heartbeat_monitor():
    """Background task to monitor kernel health"""
    global _kernel_status
    
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        
        if _kernel_status.last_heartbeat:
            time_since_heartbeat = datetime.now() - _kernel_status.last_heartbeat
            if time_since_heartbeat > timedelta(seconds=HEARTBEAT_INTERVAL * 2):
                logger.warning("[Synapse] Kernel heartbeat lost, attempting reconnect...")
                await initialize_synapse_bridge()
        
        if _kernel_status.connected:
            logger.debug(f"[Synapse] Kernel healthy - {_kernel_status.skills_available} skills available")
        else:
            logger.warning(f"[Synapse] Kernel disconnected - {_kernel_status.error_count} errors")