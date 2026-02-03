# brain/gateway/openclaw_adapter.py
# @cognitive - OpenClaw → IPPOC Adapter

from typing import Dict, Any
from brain.gateway.openclaw_mapper import map_openclaw_to_intent
from brain.gateway.openclaw_guard import guard_openclaw_request
from brain.core.autonomy import AutonomyController

_controller = None

def get_controller() -> AutonomyController:
    global _controller
    if _controller is None:
        _controller = AutonomyController()
    return _controller


async def handle_openclaw_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    The ONLY entry point OpenClaw is allowed to call.
    """
    try:
        # 1. Guardrail (canon, shape, abuse)
        guard_openclaw_request(payload)

        # 2. Map OpenClaw action → IPPOC Intent
        intent = map_openclaw_to_intent(payload)

        # 3. Inject intent into IPPOC
        controller = get_controller()
        controller.intent_stack.add(intent)

        # 4. Run one cognitive cycle
        # Note: This runs synchronously for the caller, but logically it's one tick of the brain.
        result = await controller.run_cycle()

        # 5. Normalize response for OpenClaw
        # Logic: If status is 'acted', return result. If 'rejected', return reason.
        return {
            "status": result.get("status"),
            "result": result.get("result"), # Tool output or error
            "reason": result.get("reason"),
            "intent_id": intent.intent_id
        }
    except PermissionError as e:
        return {
            "status": "refused",
            "error": str(e),
            "reason": "guard_rejection"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "reason": "adapter_crash"
        }
