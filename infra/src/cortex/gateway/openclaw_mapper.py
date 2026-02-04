# brain/gateway/openclaw_mapper.py
# @cognitive - OpenClaw Action Mapper

from cortex.core.intents import Intent, IntentType
from cortex.gateway.openclaw_plugin_map import PLUGIN_ORGAN_MAP

def map_plugin_to_intent(plugin_name: str, payload: dict) -> Intent:
    organ = PLUGIN_ORGAN_MAP.get(plugin_name)

    if organ == "body":
        intent_type = IntentType.SERVE
    elif organ == "observer":
        intent_type = IntentType.EXPLORE
    elif organ == "maintainer":
        intent_type = IntentType.MAINTAIN
    elif organ == "evolution":
        intent_type = IntentType.LEARN
    elif organ == "memory":
        intent_type = IntentType.SERVE
    elif organ == "cognition":
        intent_type = IntentType.LEARN
    elif organ == "economy":
        intent_type = IntentType.SERVE
    elif organ == "social":
        intent_type = IntentType.EXPLORE
    else:
        intent_type = IntentType.EXPLORE  # Untrusted default

    return Intent(
        description=f"OpenClaw plugin: {plugin_name}",
        intent_type=intent_type,
        priority=float(payload.get("priority", 0.5)),
        source=payload.get("source", "openclaw"),
        context=payload,
    )

def map_openclaw_to_intent(payload: dict) -> Intent:
    """
    Converts OpenClaw request into a first-class IPPOC Intent.
    """
    action_type = payload.get("type")
    source = payload.get("source", "user")
    context = payload.get("context", {})
    priority = float(payload.get("priority", 0.5))

    if action_type == "cli_command":
        # Check if we should route via body plugin logic or direct serve
        return Intent(
            description=f"Execute CLI: {context.get('cmd')}",
            intent_type=IntentType.SERVE,
            priority=priority,
            source=source,
            context=context,
        )

    if action_type == "plugin_execute":
        plugin_name = context.get("plugin", "unknown")
        return map_plugin_to_intent(plugin_name, payload)

    if action_type == "background_job":
        return Intent(
            description="Background maintenance task",
            intent_type=IntentType.MAINTAIN,
            priority=max(priority, 0.6),
            source="openclaw",
            context=context,
        )

    if action_type == "config_change":
        return Intent(
            description="System configuration change",
            intent_type=IntentType.LEARN,
            priority=priority,
            source=source,
            context=context,
        )

    # Unknown actions are exploratory, not trusted
    return Intent(
        description="Unknown OpenClaw action",
        intent_type=IntentType.EXPLORE,
        priority=0.2,
        source="openclaw",
        context=context,
    )
