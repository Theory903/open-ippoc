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

        action_type = payload.get("action_type")

        if action_type == "propose_contract":
            from brain.core.contract import WorkUnit, get_contract_manager
            
            # Parse payload
            work = WorkUnit(
                id=payload.get("id", "unknown"),
                action=payload.get("work_action", "unknown"),
                expected_value=float(payload.get("expected_value", 0.0)),
                max_cost=float(payload.get("max_cost", 0.0)),
                confidence_cap=float(payload.get("confidence", 1.0)),
                expires_at=float(payload.get("expires_at", 0.0)),
                payload=payload.get("params", {})
            )
            
            status = get_contract_manager().propose(work)
            
            if status == "accepted":
                # Map work action to intent
                from brain.core.intents import Intent, IntentType
                intent = Intent(
                    description=f"Execute contract: {work.action}",
                    intent_type=IntentType.SERVE, # Work is Service
                    priority=0.9, # Work is high priority (0.9 to pass Critical check)
                    source="openclaw_contract",
                    context={
                        "contract_id": work.contract_id,
                        "work_params": work.payload,
                        "expected_roi": work.expected_value / work.max_cost if work.max_cost > 0 else 5.0
                    }
                )
                # Proceed to execute immediately
            else:
                return {"status": "refused", "reason": status}
                
        else:
            # 2. Map other OpenClaw actions → IPPOC Intent
            intent = map_openclaw_to_intent(payload)

        # 3. Inject intent into IPPOC
        controller = get_controller()
        controller.intent_stack.add(intent)

        # 4. Run one cognitive cycle
        # Note: This runs synchronously for the caller, but logically it's one tick of the brain.
        result = await controller.run_cycle()

        # 5. Normalize response for OpenClaw
        # Logic: If status is 'acted', return result. If 'rejected', return reason.
        response = {
            "status": result.get("status"),
            "result": result.get("result"), # Tool output or error
            "reason": result.get("reason"),
            "intent_id": intent.intent_id
        }
        # Retain contract_id if present in intent context (e.g. from propose_contract)
        if intent.context and "contract_id" in intent.context:
            response["contract_id"] = intent.context["contract_id"]
            
        return response
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
