# brain/gateway/openclaw_plugin_map.py
# @cognitive - OpenClaw Plugin → IPPOC Organ Map

PLUGIN_ORGAN_MAP = {
    # Execution
    "shell": "body",
    "cli": "body",
    "filesystem": "body",
    "network": "body",

    # Perception
    "browser": "observer",
    "search": "observer",
    "metrics": "observer",
    "logs": "observer",

    # Memory
    "database": "memory",
    "vector_db": "memory",

    # Cognition
    "llm": "cognition",
    "ai_model": "cognition",

    # Maintenance
    "cron": "maintainer",
    "scheduler": "maintainer",

    # Evolution
    "git": "evolution",
    "code": "evolution",
    "test": "evolution",

    # Economy
    "wallet": "economy",
    "payment": "economy",

    # Social
    "chat": "social",
    "discord": "social",
    "slack": "social",
}

